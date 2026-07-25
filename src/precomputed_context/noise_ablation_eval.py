#!/usr/bin/env python3
"""Run a token-length-matched noise ablation for structured hints.

Motivation
----------
Structured-transfer runs compare:

    question only  vs  question + useful structured hint

This runner adds matched-noise controls:

    question only
    question + useful structured hint
    question + random meaningless text with the same tokenizer length
    question + repetitive filler with the same tokenizer length

The noise block is inserted in the same visible `Hint:` slot as the structured
hint. It is not hidden chain-of-thought and it is not produced by another LLM.
For each example, the structured hint is generated from the question text, then
the noise strings are cut to the same tokenizer length as that hint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from precomputed_context.run_context_eval import MODEL_ID, Example, parse_answer
from precomputed_context.structured_transfer_eval import (
    DATASET_INFO,
    load_requested_dataset,
    run_generation,
    structured_hint,
)


CONDITIONS = ["none", "structured", "noise_random", "noise_filler"]
NOISE_KINDS = {"noise_random", "noise_filler"}

RANDOM_NOISE_VOCAB = [
    "17",
    "4021",
    "delta",
    "mip",
    "blue",
    "77",
    "zeta",
    "blank",
    "rum",
    "901",
    "silent",
    "node",
    "4",
    "prax",
    "level",
    "002",
    "marker",
    "wisp",
    "33",
    "plain",
    "tarn",
    "8",
    "loop",
    "unused",
]

FILLER_PATTERN = "1 2 3. 3423 "


def stable_seed(run_seed: int, dataset: str, item_id: str, condition: str) -> int:
    payload = f"{run_seed}:{dataset}:{item_id}:{condition}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:16], 16)


def token_ids(tokenizer: Any, text: str) -> list[int]:
    encoded = tokenizer.encode(text)
    if hasattr(encoded, "tolist"):
        encoded = encoded.tolist()
    return list(encoded)


def token_count(tokenizer: Any | None, text: str) -> int:
    if tokenizer is None:
        return len(text.split())
    return len(token_ids(tokenizer, text))


def decode_prefix(tokenizer: Any, ids: list[int], target_tokens: int) -> str:
    if target_tokens <= 0:
        return ""
    return tokenizer.decode(ids[:target_tokens]).strip()


def make_random_noise_text(target_tokens: int, tokenizer: Any | None, seed: int) -> str:
    rng = random.Random(seed)
    pieces: list[str] = []
    while len(pieces) < max(32, target_tokens * 3):
        pieces.append(rng.choice(RANDOM_NOISE_VOCAB))
        if len(pieces) % rng.randint(5, 11) == 0:
            pieces.append(".")
    candidate = " ".join(pieces)
    if tokenizer is None:
        return " ".join(candidate.split()[:target_tokens]).strip()
    return decode_prefix(tokenizer, token_ids(tokenizer, candidate), target_tokens)


def make_filler_noise_text(target_tokens: int, tokenizer: Any | None) -> str:
    if tokenizer is None:
        return " ".join((FILLER_PATTERN.split() * max(1, target_tokens))[:target_tokens])
    candidate = FILLER_PATTERN * max(8, target_tokens * 2)
    return decode_prefix(tokenizer, token_ids(tokenizer, candidate), target_tokens)


def build_noise(
    *,
    condition: str,
    structured: str,
    tokenizer: Any | None,
    seed: int,
) -> tuple[str, dict[str, int | str]]:
    target_tokens = token_count(tokenizer, structured)
    if condition == "noise_random":
        noise = make_random_noise_text(target_tokens, tokenizer, seed)
    elif condition == "noise_filler":
        noise = make_filler_noise_text(target_tokens, tokenizer)
    else:
        raise ValueError(f"Unknown noise condition: {condition}")

    return noise, {
        "target_hint_tokens": target_tokens,
        "actual_noise_tokens": token_count(tokenizer, noise),
        "noise_kind": condition,
    }


def task_intro(example: Example) -> str:
    if example.dataset in {"prontoqa", "bbh_web_lies", "proofwriter"}:
        return "You are solving a true/false or yes/no reasoning question with lettered choices."
    return "You are solving a multiple-choice reasoning question."


def build_prompt(
    example: Example,
    condition: str,
    *,
    tokenizer: Any | None = None,
    seed: int = 0,
) -> tuple[str, str, dict[str, int | str]]:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")

    useful_hint = structured_hint(example)
    context = ""
    metadata: dict[str, int | str] = {
        "structured_hint_tokens": token_count(tokenizer, useful_hint),
        "context_tokens": 0,
        "condition": condition,
    }

    if condition == "structured":
        context = useful_hint
        metadata["context_tokens"] = token_count(tokenizer, context)
    elif condition in NOISE_KINDS:
        context, noise_metadata = build_noise(
            condition=condition,
            structured=useful_hint,
            tokenizer=tokenizer,
            seed=seed,
        )
        metadata.update(noise_metadata)
        metadata["context_tokens"] = token_count(tokenizer, context)

    prompt = f"{task_intro(example)}\n\n{example.question.strip()}\n"
    if context:
        prompt += f"\nHint:\n{context}\n"
    prompt += (
        "\nYour entire response must be exactly one of these labels: "
        f"{', '.join(example.labels)}. Do not write words or reasoning."
    )
    return prompt, context, metadata


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def pct(num: int, den: int) -> str:
    if den == 0:
        return "n/a"
    return f"{100.0 * num / den:.1f}%"


def condition_stats(records: list[dict[str, Any]], condition: str) -> tuple[int, int]:
    rows = [record for record in records if record["condition"] == condition]
    return sum(1 for row in rows if row["correct"]), len(rows)


def compare_to_none(records: list[dict[str, Any]], condition: str) -> tuple[list[str], list[str]]:
    by_item: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        by_item[record["id"]][record["condition"]] = record

    recovered: list[str] = []
    harmed: list[str] = []
    for item_id, rows in by_item.items():
        none = rows.get("none")
        other = rows.get(condition)
        if not none or not other:
            continue
        if not none["correct"] and other["correct"]:
            recovered.append(item_id)
        if none["correct"] and not other["correct"]:
            harmed.append(item_id)
    return recovered, harmed


def write_summary(path: Path, records: list[dict[str, Any]], args: argparse.Namespace, run_id: str) -> None:
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_dataset[record["dataset"]].append(record)

    lines: list[str] = []
    lines.append("# Noise Ablation Eval")
    lines.append("")
    lines.append(f"- Run id: `{run_id}`")
    lines.append(f"- Model: `{args.model}`")
    lines.append("- Thinking mode: `enable_thinking=False`")
    lines.append(f"- Conditions: `{', '.join(args.conditions)}`")
    lines.append(f"- Eval offset: `{args.eval_offset}`")
    lines.append(f"- Limit per dataset: `{args.limit}`")
    lines.append(f"- Noise seed: `{args.seed}`")
    lines.append("")
    lines.append("## What Is Being Tested")
    lines.append("")
    lines.append(
        "For every example, the structured hint is generated first. The two noise "
        "conditions then create meaningless text with the same tokenizer length as "
        "that structured hint and place it in the same visible `Hint:` block."
    )
    lines.append("")
    lines.append("| Dataset | Condition | Correct | Delta vs none | Recovered | Harmed |")
    lines.append("|---|---|---:|---:|---:|---:|")

    for dataset in sorted(by_dataset):
        dataset_records = by_dataset[dataset]
        none_correct, none_total = condition_stats(dataset_records, "none")
        for condition in args.conditions:
            correct, total = condition_stats(dataset_records, condition)
            recovered, harmed = compare_to_none(dataset_records, condition)
            delta = correct - none_correct
            recovered_cell = "n/a" if condition == "none" else f"{len(recovered)}/{none_total - none_correct}"
            harmed_cell = "n/a" if condition == "none" else f"{len(harmed)}/{none_correct}"
            lines.append(
                f"| `{dataset}` | `{condition}` | {correct}/{total} ({pct(correct, total)}) | "
                f"{delta:+d} | {recovered_cell} | {harmed_cell} |"
            )

    lines.append("")
    lines.append("## Per-Dataset Rows")
    lines.append("")
    for dataset in sorted(by_dataset):
        info = DATASET_INFO[dataset]
        dataset_records = by_dataset[dataset]
        by_item: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
        for record in dataset_records:
            by_item[record["id"]][record["condition"]] = record

        lines.append(f"### `{dataset}`")
        lines.append("")
        lines.append(f"- Source: `{info['source']}`")
        lines.append(f"- URL: {info['url']}")
        lines.append("")
        header = ["Row", "Gold", *args.conditions]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---:"] * len(header)) + "|")
        for item_id in sorted(by_item, key=lambda value: (0, int(value)) if str(value).isdigit() else (1, str(value))):
            row = by_item[item_id]
            cells = [item_id, row[args.conditions[0]]["gold"]]
            cells.extend(str(row.get(condition, {}).get("parsed")) for condition in args.conditions)
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")

    lines.append("## Token-Length Guardrail")
    lines.append("")
    lines.append(
        "Each JSONL record stores `structured_hint_tokens`, `context_tokens`, and, "
        "for noise rows, `target_hint_tokens` plus `actual_noise_tokens`. Small "
        "differences can appear if tokenizer decode/re-encode normalizes whitespace."
    )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    dataset_choices = sorted(DATASET_INFO)
    parser = argparse.ArgumentParser(
        description="Compare structured hints against same-token-length meaningless noise controls."
    )
    parser.add_argument("--datasets", nargs="+", default=dataset_choices, choices=dataset_choices)
    parser.add_argument("--conditions", nargs="+", default=CONDITIONS, choices=CONDITIONS)
    parser.add_argument("--eval-offset", type=int, default=20)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--seed", type=int, default=251001032)
    parser.add_argument("--results-dir", default="results/noise_ablation")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    conditions = list(dict.fromkeys(args.conditions))
    if "none" not in conditions:
        conditions = ["none", *conditions]
    args.conditions = conditions

    selected: dict[str, list[Example]] = {}
    for dataset in args.datasets:
        print(f"[data] loading {dataset}", flush=True)
        selected[dataset] = load_requested_dataset(dataset, args.eval_offset, args.limit)
        print(f"[data] {dataset}: selected={len(selected[dataset])}", flush=True)

    if args.dry_run:
        for dataset, examples in selected.items():
            for example in examples[:1]:
                for condition in args.conditions:
                    seed = stable_seed(args.seed, dataset, example.item_id, condition)
                    prompt, context, metadata = build_prompt(
                        example,
                        condition,
                        tokenizer=None,
                        seed=seed,
                    )
                    print(f"\n===== {dataset} row {example.item_id} / {condition} =====")
                    print(f"metadata={metadata}")
                    print(prompt)
                    if context:
                        print(f"\n[context preview]\n{context[:1000]}")
        return 0

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or f"noise_ablation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    raw_path = results_dir / f"{run_id}.jsonl"
    summary_path = results_dir / f"{run_id}.md"
    raw_path.write_text("", encoding="utf-8")

    print(f"[model] loading {args.model}", flush=True)
    from mlx_lm import load
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(args.model)
    sampler = make_sampler(temp=args.temperature)

    records: list[dict[str, Any]] = []
    for dataset, examples in selected.items():
        for index, example in enumerate(examples, start=1):
            print(f"[run] {dataset} {index}/{len(examples)} row={example.item_id}", flush=True)
            for condition in args.conditions:
                seed = stable_seed(args.seed, dataset, example.item_id, condition)
                user_prompt, context, metadata = build_prompt(
                    example,
                    condition,
                    tokenizer=tokenizer,
                    seed=seed,
                )
                started = time.perf_counter()
                raw_text = run_generation(model, tokenizer, sampler, user_prompt, args.max_tokens)
                elapsed_s = time.perf_counter() - started
                parsed = parse_answer(raw_text, example.labels)
                record = {
                    "run_id": run_id,
                    "dataset": example.dataset,
                    "source": example.source,
                    "id": example.item_id,
                    "condition": condition,
                    "gold": example.gold,
                    "parsed": parsed,
                    "correct": parsed == example.gold,
                    "raw_text": raw_text,
                    "elapsed_s": round(elapsed_s, 3),
                    "context": context,
                    "user_prompt": user_prompt,
                    "labels": example.labels,
                    **metadata,
                }
                records.append(record)
                append_jsonl(raw_path, record)

    write_summary(summary_path, records, args, run_id)
    print(f"[done] wrote {raw_path}", flush=True)
    print(f"[done] wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
