#!/usr/bin/env python3
"""Unified reader for datasets used in the precomputed-context experiments.

This file intentionally does not run the model. It only normalizes dataset
examples into the shared `Example` shape already used by the evaluation scripts.

Downstream Python interface:

    from eval_dataset_reader import (
        DATASET_GROUPS,
        list_dataset_keys,
        list_dataset_specs,
        resolve_dataset_keys,
        load_dataset,
        load_many,
        iter_examples,
        example_to_record,
        build_eval_prompt,
    )

    batch = load_dataset("bbh_date", offset=20, limit=50)
    for example in batch.examples:
        prompt, hint = build_eval_prompt(example, level="structured")

Stable example contract:

    Example.dataset  -> internal dataset key, such as "bbh_date"
    Example.source   -> source/config/split nickname
    Example.item_id  -> source row id
    Example.question -> normalized question text with lettered options
    Example.labels   -> valid output labels, usually ["A", "B", ...]
    Example.gold     -> gold label after normalization
    Example.metadata -> dataset-specific fields useful for hint builders

CLI examples:

    python eval_dataset_reader.py --list
    python eval_dataset_reader.py --show-interface
    python eval_dataset_reader.py --datasets positive50 --offset 20 --limit 2 --preview 1
    python eval_dataset_reader.py --datasets all --offset 0 --limit 5 --output data/examples.jsonl
    python eval_dataset_reader.py --datasets bbh_date prontoqa --offset 20 --limit 1 --prompt-levels none structured
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from run_context_eval import Example
from structured_transfer_eval import DATASET_INFO, build_prompt, load_requested_dataset


ALL_DATASETS = tuple(DATASET_INFO)

DATASET_GROUPS: dict[str, tuple[str, ...]] = {
    "all": ALL_DATASETS,
    "initial": ("lsat_ar", "bbh_logical_seven", "bbh_logical_five", "prontoqa"),
    "hint_lab": ("bbh_logical_seven", "lsat_ar", "prontoqa"),
    "bbh": tuple(key for key in ALL_DATASETS if key.startswith("bbh_")),
    "external": (
        "logiqa",
        "qasc",
        "openbookqa",
        "arc_challenge",
        "hellaswag",
        "winogrande",
        "proofwriter",
    ),
    "positive50": (
        "bbh_date",
        "prontoqa",
        "bbh_formal_fallacies",
        "proofwriter",
        "winogrande",
        "bbh_logical_seven",
        "reclor",
    ),
    "logic_reading": ("reclor", "logiqa", "lsat_ar"),
    "science": ("qasc", "openbookqa", "arc_challenge"),
    "rule_reasoning": ("prontoqa", "proofwriter", "bbh_formal_fallacies"),
    "commonsense": ("hellaswag", "winogrande"),
}

DATASET_ALIASES: dict[str, tuple[str, ...]] = {
    # Name used by the first context-eval script before five/seven were split.
    "bbh_logical_deduction": ("bbh_logical_seven", "bbh_logical_five"),
    "bbh_logical": ("bbh_logical_seven", "bbh_logical_five"),
    "positive": DATASET_GROUPS["positive50"],
}

INTERFACE_DOC = """# Dataset Reader Interface

Purpose:
- `eval_dataset_reader.py` is the single loading layer for datasets already used in this project.
- It reads examples from HuggingFace using the existing standard-library loaders.
- It returns normalized `Example` objects and can export those examples as JSONL.
- It does not call Qwen, does not generate hints by default, and does not write evaluation results.

Dataset selection:
- Use concrete keys from `list_dataset_keys()`, such as `bbh_date`, `prontoqa`, or `winogrande`.
- Use groups from `DATASET_GROUPS`, such as `all`, `bbh`, `external`, or `positive50`.
- Compatibility aliases include `bbh_logical_deduction`, which expands to five/seven-object BBH logical deduction.

Core Python API:
- `list_dataset_keys() -> tuple[str, ...]`
- `list_dataset_specs() -> list[dict[str, str]]`
- `resolve_dataset_keys(names: Sequence[str]) -> tuple[str, ...]`
- `load_dataset(dataset_key: str, offset: int, limit: int) -> DatasetBatch`
- `load_many(dataset_keys_or_groups: Sequence[str], offset: int, limit: int) -> dict[str, DatasetBatch]`
- `iter_examples(dataset_keys_or_groups: Sequence[str], offset: int, limit: int) -> Iterator[tuple[str, Example]]`
- `example_to_record(example: Example, include_metadata: bool = True) -> dict`
- `build_eval_prompt(example: Example, level: str = "none") -> tuple[str, str]`

Normalized `Example` fields:
- `dataset`: internal key used by hint/eval code.
- `source`: source/config/split nickname.
- `item_id`: row id or dataset id.
- `question`: normalized text with lettered options.
- `labels`: valid answer labels.
- `gold`: normalized gold answer label.
- `metadata`: dataset-specific extra fields.

JSONL export schema:
- `dataset`, `source`, `id`, `question`, `labels`, `gold`, `metadata`
- optional `prompts` and `hints` maps when `--prompt-levels` is used.

Prompt interface:
- `build_eval_prompt(example, "none")` produces the no-hint prompt used in transfer evaluation.
- `build_eval_prompt(example, "structured")` adds the transfer-only structured hint.
- Supported prompt levels are currently inherited from `structured_transfer_eval.py`: `none` and `structured`.
"""


@dataclass(frozen=True)
class DatasetBatch:
    key: str
    source: str
    url: str
    offset: int
    limit: int
    examples: list[Example]


def unique_in_order(items: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)


def list_dataset_keys() -> tuple[str, ...]:
    """Return every concrete dataset key supported by the project loaders."""
    return ALL_DATASETS


def list_dataset_specs() -> list[dict[str, str]]:
    """Return a compact catalog of concrete dataset sources."""
    specs: list[dict[str, str]] = []
    for key in list_dataset_keys():
        info = DATASET_INFO[key]
        specs.append(
            {
                "key": key,
                "source": str(info["source"]),
                "url": str(info["url"]),
                "template_seed": str(info.get("template_seed", "")),
            }
        )
    return specs


def resolve_dataset_keys(names: Sequence[str] | None) -> tuple[str, ...]:
    """Expand concrete keys, groups, and aliases into concrete dataset keys."""
    requested = list(names or ["all"])
    resolved: list[str] = []
    for name in requested:
        if name in DATASET_GROUPS:
            resolved.extend(DATASET_GROUPS[name])
        elif name in DATASET_ALIASES:
            resolved.extend(DATASET_ALIASES[name])
        elif name in DATASET_INFO:
            resolved.append(name)
        else:
            valid = sorted(set(DATASET_INFO) | set(DATASET_GROUPS) | set(DATASET_ALIASES))
            raise ValueError(f"Unknown dataset/group {name!r}. Valid values: {', '.join(valid)}")
    return unique_in_order(resolved)


def load_dataset(dataset_key: str, offset: int = 0, limit: int = 50) -> DatasetBatch:
    """Load a single normalized dataset window."""
    keys = resolve_dataset_keys([dataset_key])
    if len(keys) != 1:
        raise ValueError(f"load_dataset expects one concrete key; {dataset_key!r} expands to {keys}")
    key = keys[0]
    info = DATASET_INFO[key]
    examples = load_requested_dataset(key, offset, limit)
    return DatasetBatch(
        key=key,
        source=str(info["source"]),
        url=str(info["url"]),
        offset=offset,
        limit=limit,
        examples=examples,
    )


def load_many(
    dataset_keys_or_groups: Sequence[str] | None = None,
    *,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, DatasetBatch]:
    """Load multiple dataset windows keyed by concrete dataset key."""
    batches: dict[str, DatasetBatch] = {}
    for key in resolve_dataset_keys(dataset_keys_or_groups):
        batches[key] = load_dataset(key, offset=offset, limit=limit)
    return batches


def iter_examples(
    dataset_keys_or_groups: Sequence[str] | None = None,
    *,
    offset: int = 0,
    limit: int = 50,
) -> Iterable[tuple[str, Example]]:
    """Yield `(dataset_key, Example)` pairs for downstream experiment runners."""
    for key, batch in load_many(dataset_keys_or_groups, offset=offset, limit=limit).items():
        for example in batch.examples:
            yield key, example


def build_eval_prompt(example: Example, level: str = "none") -> tuple[str, str]:
    """Build the exact eval prompt/hint pair used by structured transfer runs."""
    return build_prompt(example, level)


def example_to_record(
    example: Example,
    *,
    include_metadata: bool = True,
    prompt_levels: Sequence[str] = (),
) -> dict[str, Any]:
    """Convert an `Example` into a JSON-serializable record.

    `prompt_levels` can include `none` and/or `structured` to materialize prompts.
    """
    record: dict[str, Any] = {
        "dataset": example.dataset,
        "source": example.source,
        "id": example.item_id,
        "question": example.question,
        "labels": example.labels,
        "gold": example.gold,
    }
    if include_metadata:
        record["metadata"] = example.metadata
    if prompt_levels:
        prompts: dict[str, str] = {}
        hints: dict[str, str] = {}
        for level in prompt_levels:
            prompt, hint = build_eval_prompt(example, level)
            prompts[level] = prompt
            hints[level] = hint
        record["prompts"] = prompts
        record["hints"] = hints
    return record


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def print_catalog() -> None:
    print("Concrete dataset keys:")
    for spec in list_dataset_specs():
        print(f"- {spec['key']}: {spec['source']} ({spec['url']})")
    print("\nGroups:")
    for name, keys in sorted(DATASET_GROUPS.items()):
        print(f"- {name}: {', '.join(keys)}")
    print("\nAliases:")
    for name, keys in sorted(DATASET_ALIASES.items()):
        print(f"- {name}: {', '.join(keys)}")


def preview_batches(
    batches: dict[str, DatasetBatch],
    *,
    preview_count: int,
    include_metadata: bool,
    prompt_levels: Sequence[str],
) -> None:
    for key, batch in batches.items():
        print(f"\n## {key}")
        print(f"source={batch.source}")
        print(f"url={batch.url}")
        print(f"window=offset {batch.offset}, limit {batch.limit}; loaded={len(batch.examples)}")
        for example in batch.examples[:preview_count]:
            record = example_to_record(
                example,
                include_metadata=include_metadata,
                prompt_levels=prompt_levels,
            )
            print(json.dumps(record, ensure_ascii=False, indent=2))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    valid_dataset_words = sorted(set(DATASET_INFO) | set(DATASET_GROUPS) | set(DATASET_ALIASES))
    parser = argparse.ArgumentParser(
        description="Read and normalize datasets used by the precomputed-context experiments.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Dataset keys/groups/aliases:\n  "
            + "\n  ".join(valid_dataset_words)
            + "\n\nUse --show-interface for the downstream Python/API contract."
        ),
    )
    parser.add_argument("--list", action="store_true", help="Print dataset catalog and exit.")
    parser.add_argument("--show-interface", action="store_true", help="Print downstream interface notes and exit.")
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["all"],
        help="Concrete dataset keys, groups, or aliases. Default: all.",
    )
    parser.add_argument("--offset", type=int, default=0, help="Rows offset for each dataset window.")
    parser.add_argument("--limit", type=int, default=5, help="Rows to load from each dataset.")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSONL export path.")
    parser.add_argument("--preview", type=int, default=1, help="Examples to print per loaded dataset.")
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="Omit dataset-specific metadata from preview/export records.",
    )
    parser.add_argument(
        "--prompt-levels",
        nargs="*",
        default=[],
        choices=["none", "structured"],
        help="Optionally include materialized eval prompts for these levels.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    if not argv:
        print_catalog()
        print("\nNo datasets were loaded. Use --datasets ... to read examples.")
        return 0

    args = parse_args(argv)
    if args.show_interface:
        print(INTERFACE_DOC.strip())
        return 0
    if args.list:
        print_catalog()
        return 0

    keys = resolve_dataset_keys(args.datasets)
    print(f"[data] loading {len(keys)} dataset(s): {', '.join(keys)}", flush=True)
    batches = load_many(keys, offset=args.offset, limit=args.limit)

    if args.output:
        def records() -> Iterable[dict[str, Any]]:
            for batch in batches.values():
                for example in batch.examples:
                    yield example_to_record(
                        example,
                        include_metadata=not args.no_metadata,
                        prompt_levels=args.prompt_levels,
                    )

        count = write_jsonl(args.output, records())
        print(f"[done] wrote {count} examples to {args.output}", flush=True)

    if args.preview > 0:
        preview_batches(
            batches,
            preview_count=args.preview,
            include_metadata=not args.no_metadata,
            prompt_levels=args.prompt_levels,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
