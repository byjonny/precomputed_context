#!/usr/bin/env python3
"""Run hand-authored hint ladders for single-example context exploration.

This is intentionally a small lab script, not a benchmark runner. The goal is to
learn which hint shapes rescue a specific example, then how far that hint can be
generalized before the model fails again.

Example:

    conda run -n qwen python -m precomputed_context.hint_lab --case bbh_34_fruit_prices
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from precomputed_context.run_context_eval import MODEL_ID, parse_answer, validate_hint


HINT_LEVELS = ["exact", "near_exact", "structured", "generalized", "minimal"]
RUN_LEVELS = ["none"] + HINT_LEVELS


def load_cases(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for case in data.get("cases", []):
        case_id = case["case_id"]
        if case_id in seen:
            raise ValueError(f"Duplicate case_id: {case_id}")
        seen.add(case_id)
        missing = set(HINT_LEVELS) - set(case.get("hints", {}))
        if missing:
            raise ValueError(f"{case_id} is missing hints: {sorted(missing)}")
        validate_case_hints(case)
    return data


def validate_case_hints(case: dict[str, Any]) -> None:
    gold = str(case["gold"]).strip().upper()
    for level, hint in case.get("hints", {}).items():
        validate_hint(hint, gold)
        label_leak_patterns = (
            rf"\({re.escape(gold)}\)",
            rf"\b(?:option|choice|letter)\s+{re.escape(gold)}\b",
            rf"\b{re.escape(gold)}\s*(?:is|=)\s*(?:true|false|correct|valid)\b",
        )
        for pattern in label_leak_patterns:
            if re.search(pattern, hint, flags=re.IGNORECASE):
                raise ValueError(
                    f"{case['case_id']}:{level} appears to leak gold label {gold}: {hint}"
                )


def select_cases(data: dict[str, Any], case_ids: list[str], datasets: list[str]) -> list[dict[str, Any]]:
    cases = list(data.get("cases", []))
    if case_ids:
        wanted = set(case_ids)
        cases = [case for case in cases if case["case_id"] in wanted]
        missing = wanted - {case["case_id"] for case in cases}
        if missing:
            raise ValueError(f"Unknown case ids: {sorted(missing)}")
    if datasets:
        wanted_datasets = set(datasets)
        cases = [case for case in cases if case["dataset"] in wanted_datasets]
    return cases


def expand_levels(levels: list[str]) -> list[str]:
    if not levels or "all" in levels:
        return RUN_LEVELS
    out: list[str] = []
    for level in levels:
        if level not in RUN_LEVELS:
            raise ValueError(f"Unknown level {level!r}; expected one of {RUN_LEVELS}")
        if level not in out:
            out.append(level)
    return out


def build_user_prompt(case: dict[str, Any], level: str) -> tuple[str, str]:
    hint = "" if level == "none" else case["hints"][level]
    prompt = f"{case['task']}\n\n{case['question'].strip()}\n"
    if hint:
        prompt += f"\nHint:\n{hint}\n"
    prompt += (
        "\nYour entire response must be exactly one of these labels: "
        f"{', '.join(case['labels'])}. Do not write words or reasoning."
    )
    return prompt, hint


def run_generation(model: Any, tokenizer: Any, sampler: Any, user_prompt: str, max_tokens: int) -> str:
    from mlx_lm import generate

    messages = [
        {
            "role": "system",
            "content": "Output exactly one capital letter for the selected choice. Nothing else.",
        },
        {"role": "user", "content": user_prompt},
    ]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    return generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        sampler=sampler,
        verbose=False,
    )


def make_record(
    *,
    run_id: str,
    case: dict[str, Any],
    level: str,
    repeat_index: int,
    hint: str,
    user_prompt: str,
    raw_text: str,
    elapsed_s: float,
    model_id: str,
) -> dict[str, Any]:
    parsed = parse_answer(raw_text, list(case["labels"]))
    return {
        "run_id": run_id,
        "case_id": case["case_id"],
        "dataset": case["dataset"],
        "source": case["source"],
        "item_id": case["item_id"],
        "hint_level": level,
        "repeat_index": repeat_index,
        "gold": case["gold"],
        "parsed": parsed,
        "correct": parsed == case["gold"],
        "raw_text": raw_text,
        "elapsed_s": round(elapsed_s, 3),
        "model": model_id,
        "hint": hint,
        "user_prompt": user_prompt,
    }


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def level_records(records: list[dict[str, Any]], case_id: str, level: str) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record["case_id"] == case_id and record["hint_level"] == level
    ]


def level_cell(records: list[dict[str, Any]], case_id: str, level: str) -> str:
    rows = level_records(records, case_id, level)
    if not rows:
        return "not run"
    correct = sum(1 for row in rows if row["correct"])
    outputs = sorted({str(row["parsed"]) for row in rows})
    raw_outputs = sorted({str(row["raw_text"]).strip() for row in rows})
    shown_outputs = ", ".join(outputs) if outputs != ["None"] else ", ".join(raw_outputs)
    return f"{correct}/{len(rows)} ({shown_outputs})"


def stable_correct(records: list[dict[str, Any]], case_id: str, level: str, repeats: int) -> bool:
    rows = level_records(records, case_id, level)
    return len(rows) == repeats and all(row["correct"] for row in rows)


def most_general_stable(records: list[dict[str, Any]], case_id: str, repeats: int) -> tuple[str, str]:
    stable = [level for level in HINT_LEVELS if stable_correct(records, case_id, level, repeats)]
    if not stable:
        return "none", "exact failed or was not run"

    best = stable[-1]
    best_index = HINT_LEVELS.index(best)
    boundary = "no more-general level in this run"
    for level in HINT_LEVELS[best_index + 1 :]:
        rows = level_records(records, case_id, level)
        if rows and not stable_correct(records, case_id, level, repeats):
            boundary = level
            break
    return best, boundary


def write_summary(
    *,
    path: Path,
    run_id: str,
    cases: list[dict[str, Any]],
    records: list[dict[str, Any]],
    args: argparse.Namespace,
    levels: list[str],
) -> None:
    lines: list[str] = []
    lines.append("# Hint Lab Summary")
    lines.append("")
    lines.append(f"- Run id: `{run_id}`")
    lines.append(f"- Model: `{args.model}`")
    lines.append("- Thinking mode: `enable_thinking=False`")
    lines.append(f"- Repeats per level: `{args.repeats}`")
    lines.append(f"- Levels: `{', '.join(levels)}`")
    lines.append("")
    lines.append("| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable | Failure boundary |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|")

    for case in cases:
        baseline = case.get("baseline_observation", {})
        baseline_text = str(baseline.get("parsed", "unknown"))
        best, boundary = most_general_stable(records, case["case_id"], args.repeats)
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{case['case_id']}`",
                    case["dataset"],
                    baseline_text,
                    case["gold"],
                    level_cell(records, case["case_id"], "exact"),
                    level_cell(records, case["case_id"], "near_exact"),
                    level_cell(records, case["case_id"], "structured"),
                    level_cell(records, case["case_id"], "generalized"),
                    level_cell(records, case["case_id"], "minimal"),
                    best,
                    boundary,
                ]
            )
            + " |"
        )

    lines.append("")
    lines.append("## Per-Case Notes")
    lines.append("")
    for case in cases:
        lines.append(f"### `{case['case_id']}`")
        lines.append("")
        lines.append(f"- Gold: `{case['gold']}`")
        baseline = case.get("baseline_observation", {})
        if baseline:
            lines.append(
                f"- Prior baseline: raw `{baseline.get('raw_text')}`, parsed `{baseline.get('parsed')}`"
            )
        for level in levels:
            rows = level_records(records, case["case_id"], level)
            if not rows:
                continue
            outputs = ", ".join(
                f"r{row['repeat_index']}={row['parsed'] or row['raw_text']!r}"
                for row in rows
            )
            lines.append(f"- `{level}`: {outputs}")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def update_cases_file(
    *,
    cases_path: Path,
    data: dict[str, Any],
    run_id: str,
    records: list[dict[str, Any]],
    summary_path: Path,
    raw_path: Path,
) -> None:
    compact_records = [
        {
            "case_id": record["case_id"],
            "hint_level": record["hint_level"],
            "repeat_index": record["repeat_index"],
            "parsed": record["parsed"],
            "correct": record["correct"],
            "raw_text": record["raw_text"],
        }
        for record in records
    ]
    data.setdefault("run_history", []).append(
        {
            "run_id": run_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "raw_path": str(raw_path),
            "summary_path": str(summary_path),
            "records": compact_records,
        }
    )
    cases_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def print_case_list(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        baseline = case.get("baseline_observation", {})
        print(
            f"{case['case_id']}\t{case['dataset']}\tgold={case['gold']}\t"
            f"baseline={baseline.get('parsed', 'unknown')}"
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hand-authored precomputed-context hint ladders.")
    parser.add_argument("--cases-file", default="data/hint_cases.json")
    parser.add_argument("--case", nargs="+", default=[], help="Case ids to run. Defaults to all cases.")
    parser.add_argument("--dataset", nargs="+", default=[], help="Dataset names to run.")
    parser.add_argument(
        "--levels",
        nargs="+",
        default=["all"],
        help=f"Levels to run: all or any of {', '.join(RUN_LEVELS)}.",
    )
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--results-dir", default="results/hint_lab")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--list", action="store_true", help="List cases and exit.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print prompts without loading the model.")
    parser.add_argument("--update-cases", action="store_true", help="Append compact run history to the cases JSON file.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    cases_path = Path(args.cases_file)
    data = load_cases(cases_path)
    cases = select_cases(data, args.case, args.dataset)
    levels = expand_levels(args.levels)

    if args.list:
        print_case_list(cases)
        return 0
    if not cases:
        raise ValueError("No cases selected.")
    if args.repeats < 1:
        raise ValueError("--repeats must be >= 1")

    if args.dry_run:
        for case in cases:
            for level in levels:
                prompt, _ = build_user_prompt(case, level)
                print(f"\n===== {case['case_id']} / {level} =====\n{prompt}")
        return 0

    run_id = args.run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    raw_path = results_dir / f"{run_id}.jsonl"
    summary_path = results_dir / f"{run_id}.md"
    raw_path.write_text("", encoding="utf-8")

    print(f"[model] loading {args.model}", flush=True)
    from mlx_lm import load
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(args.model)
    sampler = make_sampler(temp=args.temperature)

    records: list[dict[str, Any]] = []
    for case in cases:
        for level in levels:
            user_prompt, hint = build_user_prompt(case, level)
            for repeat_index in range(1, args.repeats + 1):
                print(
                    f"[run] {case['case_id']} level={level} repeat={repeat_index}/{args.repeats}",
                    flush=True,
                )
                started = time.perf_counter()
                raw_text = run_generation(model, tokenizer, sampler, user_prompt, args.max_tokens)
                elapsed_s = time.perf_counter() - started
                record = make_record(
                    run_id=run_id,
                    case=case,
                    level=level,
                    repeat_index=repeat_index,
                    hint=hint,
                    user_prompt=user_prompt,
                    raw_text=raw_text,
                    elapsed_s=elapsed_s,
                    model_id=args.model,
                )
                records.append(record)
                append_jsonl(raw_path, record)

    write_summary(
        path=summary_path,
        run_id=run_id,
        cases=cases,
        records=records,
        args=args,
        levels=levels,
    )

    if args.update_cases:
        update_cases_file(
            cases_path=cases_path,
            data=data,
            run_id=run_id,
            records=records,
            summary_path=summary_path,
            raw_path=raw_path,
        )

    print(f"[done] wrote {raw_path}", flush=True)
    print(f"[done] wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
