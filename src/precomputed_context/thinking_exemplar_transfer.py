#!/usr/bin/env python3
"""Transfer one thinking-mode BBH date example into non-thinking evaluation.

Experiment shape:
1. Load one BBH date_understanding example as the solved exemplar.
2. Run Qwen with `enable_thinking=True` on that exemplar and save the generated
   thinking trace plus final answer.
3. Evaluate later BBH date_understanding examples with `enable_thinking=False`
   under two conditions:
   - `none`: just the new question.
   - `thinking_exemplar`: the solved exemplar question, its full thinking trace,
     and its final answer are prepended before the new question.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from precomputed_context.eval_dataset_reader import load_dataset
from precomputed_context.run_context_eval import MODEL_ID, Example, parse_answer


CONDITIONS = ("none", "thinking_exemplar")


def format_labels(labels: Sequence[str]) -> str:
    return ", ".join(labels)


def build_exemplar_prompt(example: Example) -> str:
    return (
        "You are solving a multiple-choice date-understanding question.\n"
        "Write the complete reasoning, but keep it concise. The very last line "
        "must be exactly `Final answer: <letter>`.\n\n"
        f"{example.question.strip()}\n"
    )


def build_eval_prompt(
    example: Example,
    *,
    condition: str,
    exemplar: Example,
    exemplar_thinking: str,
    exemplar_answer_text: str,
) -> str:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")

    prefix = "You are solving a multiple-choice date-understanding question.\n\n"
    if condition == "thinking_exemplar":
        prefix += (
            "Below is one solved example from the same task. Use it as a "
            "transferable pattern for date arithmetic, but do not copy its "
            "answer for the new question.\n\n"
            "Solved example question:\n"
            f"{exemplar.question.strip()}\n\n"
            "Solved example thinking trace:\n"
            f"{exemplar_thinking.strip()}\n\n"
            "Solved example final answer:\n"
            f"{exemplar_answer_text.strip()}\n\n"
            "Now answer the new question.\n\n"
        )

    return (
        f"{prefix}{example.question.strip()}\n\n"
        "Your entire response must be exactly one of these labels: "
        f"{format_labels(example.labels)}. Do not write words or reasoning."
    )


def apply_chat_template(tokenizer: Any, user_prompt: str, *, enable_thinking: bool) -> str:
    system = "Output the requested answer format exactly."
    if not enable_thinking:
        system = "Output exactly one capital letter for the selected choice. Nothing else."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_prompt},
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=enable_thinking,
    )


def run_generation(
    model: Any,
    tokenizer: Any,
    sampler: Any,
    user_prompt: str,
    *,
    enable_thinking: bool,
    max_tokens: int,
) -> str:
    from mlx_lm import generate

    prompt = apply_chat_template(tokenizer, user_prompt, enable_thinking=enable_thinking)
    return generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        sampler=sampler,
        verbose=False,
    )


def parse_final_answer(text: str, labels: Sequence[str]) -> str | None:
    valid = set(labels)
    patterns = (
        r"\bfinal\s+answer\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
        r"\banswer\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
        r"\boption\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
    )
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for letter in reversed(matches):
            letter = letter.upper()
            if letter in valid:
                return letter

    if "</think>" in text:
        tail = text.rsplit("</think>", 1)[1]
        parsed = parse_answer(tail, list(labels))
        if parsed:
            return parsed

    letters = [letter.upper() for letter in re.findall(r"\b([A-Z])\b", text) if letter.upper() in valid]
    return letters[-1] if letters else None


def split_thinking_output(text: str, parsed_answer: str | None = None) -> tuple[str, str]:
    """Return `(thinking_content, final_answer_text)` from a thinking-mode output."""
    if "<think>" in text and "</think>" in text:
        thinking = text.split("<think>", 1)[1].split("</think>", 1)[0].strip()
        answer_text = text.rsplit("</think>", 1)[1].strip()
        if parsed_answer and not re.search(r"\bfinal\s+answer\b", answer_text, flags=re.IGNORECASE):
            answer_text = f"Final answer: {parsed_answer}"
        return thinking, answer_text
    if "</think>" in text:
        thinking, answer_text = text.split("</think>", 1)
        thinking = thinking.replace("<think>", "").strip()
        if parsed_answer and not re.search(r"\bfinal\s+answer\b", answer_text, flags=re.IGNORECASE):
            answer_text = f"Final answer: {parsed_answer}"
        return thinking, answer_text.strip()
    final_match = re.search(
        r"\bfinal\s+answer\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
        text,
        flags=re.IGNORECASE,
    )
    if final_match:
        thinking = text[: final_match.start()].strip()
        answer_text = text[final_match.start() :].strip()
        return thinking, answer_text
    if parsed_answer:
        return text.strip(), f"Final answer: {parsed_answer}"
    return text.strip(), text.strip()


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def write_exemplar(path: Path, record: dict[str, Any]) -> None:
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_eval_record(
    *,
    run_id: str,
    example: Example,
    condition: str,
    user_prompt: str,
    raw_text: str,
    elapsed_s: float,
) -> dict[str, Any]:
    parsed = parse_answer(raw_text, example.labels)
    return {
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
        "user_prompt": user_prompt,
        "labels": example.labels,
    }


def stats(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_id: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    by_condition: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_condition[record["condition"]].append(record)
        by_id[str(record["id"])][record["condition"]] = record

    out: dict[str, Any] = {"conditions": {}, "recovered": [], "harmed": []}
    for condition in CONDITIONS:
        rows = by_condition.get(condition, [])
        correct = sum(1 for row in rows if row["correct"])
        out["conditions"][condition] = {
            "correct": correct,
            "total": len(rows),
            "accuracy": correct / len(rows) if rows else 0.0,
        }

    for item_id, cond in by_id.items():
        if not all(condition in cond for condition in CONDITIONS):
            continue
        none = cond["none"]
        exemplar = cond["thinking_exemplar"]
        if not none["correct"] and exemplar["correct"]:
            out["recovered"].append(item_id)
        if none["correct"] and not exemplar["correct"]:
            out["harmed"].append(item_id)
    return out


def write_summary(
    path: Path,
    *,
    run_id: str,
    args: argparse.Namespace,
    exemplar_record: dict[str, Any],
    records: list[dict[str, Any]],
    raw_path: Path,
    exemplar_path: Path,
) -> None:
    st = stats(records)
    none = st["conditions"]["none"]
    ctx = st["conditions"]["thinking_exemplar"]
    delta = ctx["correct"] - none["correct"]
    lines = [
        "# Thinking-Exemplar Transfer: BBH date_understanding",
        "",
        f"- Run id: `{run_id}`",
        f"- Model: `{args.model}`",
        "- Exemplar generation: `enable_thinking=True`",
        "- Evaluation generation: `enable_thinking=False`",
        f"- Exemplar row: `{exemplar_record['id']}`",
        f"- Eval window: offset `{args.eval_offset}`, limit `{args.limit}`",
        f"- Exemplar parsed answer: `{exemplar_record['parsed_answer']}`; gold: `{exemplar_record['gold']}`; correct: `{exemplar_record['correct']}`",
        "",
        "## Accuracy",
        "",
        "| Condition | Correct | Accuracy |",
        "|---|---:|---:|",
        f"| none | {none['correct']}/{none['total']} | {none['accuracy']:.1%} |",
        f"| thinking_exemplar | {ctx['correct']}/{ctx['total']} | {ctx['accuracy']:.1%} |",
        f"| delta | {delta:+d} | {(ctx['accuracy'] - none['accuracy']):+.1%} |",
        "",
        "## Movement",
        "",
        f"- Recovered: `{', '.join(st['recovered']) or '-'}`",
        f"- Harmed: `{', '.join(st['harmed']) or '-'}`",
        "",
        "## Artifacts",
        "",
        f"- Exemplar thinking JSON: `{exemplar_path}`",
        f"- Raw evaluation JSONL: `{raw_path}`",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Use one Qwen thinking-mode BBH date example as context for non-thinking evaluation."
    )
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--exemplar-offset", type=int, default=20)
    parser.add_argument("--eval-offset", type=int, default=21)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--thinking-max-tokens", type=int, default=1024)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--results-dir", default="results/thinking_exemplar_transfer")
    parser.add_argument("--run-id", default="")
    parser.add_argument(
        "--reuse-exemplar-json",
        type=Path,
        default=None,
        help="Reuse a previously saved exemplar JSON instead of regenerating thinking.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Build prompts but do not load the model.")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or f"thinking_exemplar_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    raw_path = results_dir / f"{run_id}.jsonl"
    exemplar_path = results_dir / f"{run_id}_exemplar.json"
    summary_path = results_dir / f"{run_id}.md"

    if args.reuse_exemplar_json:
        saved_exemplar = json.loads(args.reuse_exemplar_json.read_text(encoding="utf-8"))
        exemplar = Example(
            dataset=saved_exemplar["dataset"],
            source=saved_exemplar["source"],
            item_id=saved_exemplar["id"],
            question=saved_exemplar["question"],
            labels=list(saved_exemplar["labels"]),
            gold=saved_exemplar["gold"],
            metadata=saved_exemplar.get("metadata", {}),
        )
    else:
        exemplar_batch = load_dataset("bbh_date", offset=args.exemplar_offset, limit=1)
        if not exemplar_batch.examples:
            raise RuntimeError("No exemplar example loaded.")
        exemplar = exemplar_batch.examples[0]
    eval_examples = load_dataset("bbh_date", offset=args.eval_offset, limit=args.limit).examples
    eval_examples = [example for example in eval_examples if example.item_id != exemplar.item_id]

    if args.dry_run:
        fake_thinking = "Example thinking would be generated here."
        fake_answer = "Final answer: A"
        print("===== exemplar thinking prompt =====")
        print(build_exemplar_prompt(exemplar))
        for condition in CONDITIONS:
            print(f"\n===== eval prompt / {condition} =====")
            print(
                build_eval_prompt(
                    eval_examples[0],
                    condition=condition,
                    exemplar=exemplar,
                    exemplar_thinking=fake_thinking,
                    exemplar_answer_text=fake_answer,
                )
            )
        return 0

    print(f"[model] loading {args.model}", flush=True)
    from mlx_lm import load
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(args.model)
    sampler = make_sampler(temp=args.temperature)

    if args.reuse_exemplar_json:
        print(f"[exemplar] reusing {args.reuse_exemplar_json}", flush=True)
        parsed_answer = saved_exemplar.get("parsed_answer")
        thinking = str(saved_exemplar["thinking"]).strip()
        answer_text = str(saved_exemplar.get("answer_text", "")).strip()
        if parsed_answer and not re.search(r"\bfinal\s+answer\b", answer_text, flags=re.IGNORECASE):
            answer_text = f"Final answer: {parsed_answer}"
        exemplar_record = dict(saved_exemplar)
        exemplar_record.update(
            {
                "run_id": run_id,
                "answer_text": answer_text,
                "reuse_source": str(args.reuse_exemplar_json),
            }
        )
    else:
        exemplar_prompt = build_exemplar_prompt(exemplar)
        print(f"[exemplar] bbh_date row={exemplar.item_id}", flush=True)
        started = time.perf_counter()
        exemplar_raw = run_generation(
            model,
            tokenizer,
            sampler,
            exemplar_prompt,
            enable_thinking=True,
            max_tokens=args.thinking_max_tokens,
        )
        exemplar_elapsed = time.perf_counter() - started
        parsed_answer = parse_final_answer(exemplar_raw, exemplar.labels)
        thinking, answer_text = split_thinking_output(exemplar_raw, parsed_answer)
        exemplar_record = {
            "run_id": run_id,
            "dataset": exemplar.dataset,
            "source": exemplar.source,
            "id": exemplar.item_id,
            "question": exemplar.question,
            "labels": exemplar.labels,
            "gold": exemplar.gold,
            "thinking_prompt": exemplar_prompt,
            "raw_text": exemplar_raw,
            "thinking": thinking,
            "answer_text": answer_text,
            "parsed_answer": parsed_answer,
            "correct": parsed_answer == exemplar.gold,
            "elapsed_s": round(exemplar_elapsed, 3),
            "enable_thinking": True,
        }
    write_exemplar(exemplar_path, exemplar_record)

    raw_path.write_text("", encoding="utf-8")
    records: list[dict[str, Any]] = []
    for index, example in enumerate(eval_examples, start=1):
        print(f"[eval] {index}/{len(eval_examples)} row={example.item_id}", flush=True)
        for condition in CONDITIONS:
            user_prompt = build_eval_prompt(
                example,
                condition=condition,
                exemplar=exemplar,
                exemplar_thinking=thinking,
                exemplar_answer_text=answer_text or f"Final answer: {parsed_answer}",
            )
            started = time.perf_counter()
            raw_text = run_generation(
                model,
                tokenizer,
                sampler,
                user_prompt,
                enable_thinking=False,
                max_tokens=args.max_tokens,
            )
            elapsed = time.perf_counter() - started
            record = make_eval_record(
                run_id=run_id,
                example=example,
                condition=condition,
                user_prompt=user_prompt,
                raw_text=raw_text,
                elapsed_s=elapsed,
            )
            records.append(record)
            append_jsonl(raw_path, record)

    write_summary(
        summary_path,
        run_id=run_id,
        args=args,
        exemplar_record=exemplar_record,
        records=records,
        raw_path=raw_path,
        exemplar_path=exemplar_path,
    )
    print(f"[done] wrote {exemplar_path}", flush=True)
    print(f"[done] wrote {raw_path}", flush=True)
    print(f"[done] wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
