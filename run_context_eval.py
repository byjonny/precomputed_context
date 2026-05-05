#!/usr/bin/env python3
"""Evaluate no-answer precomputed context with Qwen non-thinking mode.

This script intentionally uses only the Python standard library plus mlx_lm.
Run it from the qwen conda environment, for example:

    conda run -n qwen python run_context_eval.py
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MODEL_ID = "Qwen/Qwen3.5-4B"
SEED = 20260424
LEVELS = ("none", "generic_hint", "structured_hint", "guided_hint")
NON_EMPTY_LEVELS = ("generic_hint", "structured_hint", "guided_hint")
HF_ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"
USER_AGENT = "precomputed-context-eval/0.1"


@dataclass(frozen=True)
class Example:
    dataset: str
    source: str
    item_id: str
    question: str
    labels: list[str]
    gold: str
    metadata: dict[str, Any]

    @property
    def key(self) -> str:
        return f"{self.dataset}::{self.source}::{self.item_id}"


def read_url_text(url: str, timeout: int = 60, retries: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset)
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def read_url_json(url: str, timeout: int = 60, retries: int = 3) -> Any:
    return json.loads(read_url_text(url, timeout=timeout, retries=retries))


def fetch_hf_rows(dataset: str, config: str, split: str = "test") -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    offset = 0
    page_size = 100

    while True:
        params = {
            "dataset": dataset,
            "config": config,
            "split": split,
            "offset": offset,
            "length": page_size,
        }
        url = f"{HF_ROWS_ENDPOINT}?{urlencode(params)}"
        data = read_url_json(url)
        page = data.get("rows", [])
        if not page:
            break

        for item in page:
            rows.append((int(item["row_idx"]), item["row"]))

        offset += len(page)
        total = data.get("num_rows_total")
        if total is not None and offset >= int(total):
            break
        if len(page) < page_size:
            break

    return rows


def unique_in_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def labels_from_text(text: str, default_count: int) -> list[str]:
    labels = unique_in_order(re.findall(r"\(([A-Z])\)", text))
    if labels:
        return labels
    return [chr(ord("A") + i) for i in range(default_count)]


def strip_lsat_answer_cue(text: str) -> str:
    return re.sub(
        r"\nA:\s*Among\s+[A-Z]\s+through\s+[A-Z],\s*the answer is\s*$",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )


def load_lsat_ar() -> list[Example]:
    examples: list[Example] = []
    rows = fetch_hf_rows("hails/agieval-lsat-ar", "default", "test")
    for row_idx, row in rows:
        labels = [chr(ord("A") + i) for i in range(len(row["choices"]))]
        gold_idx = int(row["gold"][0])
        examples.append(
            Example(
                dataset="lsat_ar",
                source="agieval_lsat_ar",
                item_id=str(row_idx),
                question=strip_lsat_answer_cue(str(row["query"])),
                labels=labels,
                gold=labels[gold_idx],
                metadata={"choices": row["choices"]},
            )
        )
    return examples


def parse_bbh_target(target: str) -> str:
    match = re.search(r"\(([A-Z])\)", target)
    if match:
        return match.group(1)
    match = re.search(r"\b([A-Z])\b", target.strip())
    if match:
        return match.group(1)
    raise ValueError(f"Could not parse BBH target: {target!r}")


def load_bbh_config(config: str, source: str) -> list[Example]:
    examples: list[Example] = []
    rows = fetch_hf_rows("lukaemon/bbh", config, "test")
    for row_idx, row in rows:
        question = str(row["input"]).strip()
        labels = labels_from_text(question, default_count=7)
        examples.append(
            Example(
                dataset="bbh_logical_deduction",
                source=source,
                item_id=str(row_idx),
                question=question,
                labels=labels,
                gold=parse_bbh_target(str(row["target"])),
                metadata={"config": config},
            )
        )
    return examples


def load_bbh_primary_and_fallback() -> tuple[list[Example], list[Example]]:
    primary = load_bbh_config(
        "logical_deduction_seven_objects",
        "bbh_logical_deduction_seven_objects",
    )
    fallback = load_bbh_config(
        "logical_deduction_five_objects",
        "bbh_logical_deduction_five_objects",
    )
    return primary, fallback


def load_prontoqa() -> list[Example]:
    url = "https://huggingface.co/datasets/renma/ProntoQA/resolve/main/ProntoQA_dev_gpt-4.json"
    rows = read_url_json(url)
    examples: list[Example] = []
    for idx, row in enumerate(rows):
        options = [str(option).strip() for option in row["options"]]
        labels = labels_from_text("\n".join(options), default_count=len(options))
        context = str(row["context"]).strip()
        question = str(row["question"]).strip()
        prompt_text = f"Context:\n{context}\n\nQuestion:\n{question}\n\nOptions:\n" + "\n".join(options)
        examples.append(
            Example(
                dataset="prontoqa",
                source="prontoqa_dev_gpt4",
                item_id=str(row.get("id", idx)),
                question=prompt_text,
                labels=labels,
                gold=str(row["answer"]).strip().upper(),
                metadata={"context": context, "question": question, "options": options},
            )
        )
    return examples


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+", text.strip())
    return [piece.strip() for piece in pieces if piece.strip()]


def trim(text: str, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def extract_lsat_parts(question: str) -> dict[str, Any]:
    setup = question
    conditions = ""
    focus = ""

    marker = "according to the following conditions:"
    if marker in question:
        setup, rest = question.split(marker, 1)
        if "Q:" in rest:
            conditions, tail = rest.split("Q:", 1)
        else:
            conditions, tail = rest, ""
    else:
        tail = question

    focus_match = re.search(r"Q:\s*(.*?)(?:Answer Choices:|Options:|$)", question, re.DOTALL)
    if focus_match:
        focus = trim(focus_match.group(1), 500)
    elif tail:
        focus = trim(tail, 500)

    rules = split_sentences(conditions)
    return {
        "setup": trim(setup, 600),
        "rules": rules[:12],
        "focus": focus,
    }


def extract_bbh_parts(question: str) -> dict[str, Any]:
    problem = question.split("Options:", 1)[0].strip()
    sentences = split_sentences(problem)
    entity_text = ""
    entity_match = re.search(r":\s*([^.]+)\.", problem)
    if entity_match:
        entity_text = trim(entity_match.group(1), 300)

    fact_sentences = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
    ]
    fixed_words = (
        "first",
        "second",
        "third",
        "fourth",
        "fifth",
        "sixth",
        "seventh",
        "last",
    )
    relation_words = (
        "above",
        "below",
        "older",
        "newer",
        "higher",
        "lower",
        "larger",
        "smaller",
        "before",
        "after",
    )
    fixed = [s for s in fact_sentences if any(word in s.lower() for word in fixed_words)]
    comparisons = [s for s in fact_sentences if any(word in s.lower() for word in relation_words)]
    return {
        "entities": entity_text,
        "fixed": fixed[:8],
        "comparisons": comparisons[:12],
    }


def extract_pronto_parts(example: Example) -> dict[str, Any]:
    context = str(example.metadata.get("context", ""))
    question = str(example.metadata.get("question", ""))
    query_statement = question
    match = re.search(r"\?\s*(.+?)\.?\s*$", question)
    if match:
        query_statement = match.group(1).strip().rstrip(".")

    subject = ""
    predicate = ""
    statement_match = re.match(r"([A-Z][A-Za-z]*)\s+(?:is|are)\s+(.+)", query_statement)
    if statement_match:
        subject = statement_match.group(1)
        predicate = statement_match.group(2).strip()

    sentences = split_sentences(context)
    relevant: list[str] = []
    predicate_token = predicate.replace("not ", "").split()[0].lower() if predicate else ""
    for sentence in sentences:
        lowered = sentence.lower()
        if subject and subject.lower() in lowered:
            relevant.append(sentence)
        elif predicate_token and predicate_token in lowered:
            relevant.append(sentence)

    return {
        "query_statement": query_statement,
        "subject": subject,
        "predicate": predicate,
        "relevant": unique_in_order(relevant)[:8],
    }


def generic_hint(example: Example) -> str:
    if example.dataset == "lsat_ar":
        return (
            "Use a compact diagram before choosing. Separate hard placement rules, "
            "negative rules, and conditional rules. For complete schedule choices, "
            "check every condition literally; for must-be-true questions, track all "
            "remaining legal possibilities."
        )
    if example.dataset == "bbh_logical_deduction":
        return (
            "Represent the order as numbered ranks. Convert each comparison into a "
            "directional inequality and place fixed-rank facts first. Then test the "
            "listed choices against the resulting partial order."
        )
    if example.dataset == "prontoqa":
        return (
            "Do forward chaining from the named individual. Apply only one-way rules "
            "whose premise is already known, preserve negation, and compare the final "
            "derived property with the queried statement."
        )
    raise ValueError(f"Unknown dataset: {example.dataset}")


def structured_hint(example: Example) -> str:
    if example.dataset == "lsat_ar":
        parts = extract_lsat_parts(example.question)
        rules = "\n".join(f"- {trim(rule, 220)}" for rule in parts["rules"])
        return (
            "Precomputed structure:\n"
            f"- Puzzle setup: {parts['setup']}\n"
            f"- Question focus: {parts['focus']}\n"
            "- Encode these constraints before checking choices:\n"
            f"{rules}"
        )
    if example.dataset == "bbh_logical_deduction":
        parts = extract_bbh_parts(example.question)
        fixed = "\n".join(f"- {trim(item, 180)}" for item in parts["fixed"]) or "- None explicit."
        comparisons = "\n".join(f"- {trim(item, 180)}" for item in parts["comparisons"]) or "- None explicit."
        return (
            "Precomputed structure:\n"
            f"- Ordered objects: {parts['entities']}\n"
            "- Fixed-position facts:\n"
            f"{fixed}\n"
            "- Directional comparisons:\n"
            f"{comparisons}"
        )
    if example.dataset == "prontoqa":
        parts = extract_pronto_parts(example)
        relevant = "\n".join(f"- {trim(item, 180)}" for item in parts["relevant"]) or "- No direct lexical match; use the full context chain."
        subject = parts["subject"] or "the named subject"
        predicate = parts["predicate"] or "the queried property"
        return (
            "Precomputed structure:\n"
            f"- Query statement: {parts['query_statement']}\n"
            f"- Start from facts about: {subject}\n"
            f"- Target property to compare: {predicate}\n"
            "- Context sentences to keep especially visible:\n"
            f"{relevant}"
        )
    raise ValueError(f"Unknown dataset: {example.dataset}")


def guided_hint(example: Example) -> str:
    if example.dataset == "lsat_ar":
        return (
            "Guided check list:\n"
            "- Draw the slots or table with one cell per position.\n"
            "- Apply absolute placement, capacity, and adjacency constraints before choices.\n"
            "- Treat each conditional as inactive until its trigger is present.\n"
            "- When testing a choice, scan the original rules one by one and stop only after all pass.\n"
            "- For a must-be-true target, compare what remains common across every legal arrangement."
        )
    if example.dataset == "bbh_logical_deduction":
        return (
            "Guided check list:\n"
            "- Decide which end of the rank scale is rank 1 from the wording.\n"
            "- Write fixed-rank facts as exact equalities.\n"
            "- Write each comparison as an inequality without reversing it.\n"
            "- For each listed choice, temporarily add that claim and check whether all equalities and inequalities can still hold.\n"
            "- Prefer consistency checking over trying to narrate the whole order."
        )
    if example.dataset == "prontoqa":
        return (
            "Guided check list:\n"
            "- Put the subject's known classes and properties into a working set.\n"
            "- Repeatedly add conclusions from rules whose left side is already in the working set.\n"
            "- Do not use a rule backward; X implies Y does not mean Y implies X.\n"
            "- Keep positive and negated properties distinct.\n"
            "- Match the derived queried property against the two truth-value choices."
        )
    raise ValueError(f"Unknown dataset: {example.dataset}")


BANNED_HINT_PATTERNS = (
    r"\banswer is\b",
    r"\bcorrect option\b",
    r"\bfinal answer\b",
    r"\bgold\b",
    r"\bchoose\s+\(?[A-Z]\)?\b",
    r"\bselect\s+\(?[A-Z]\)?\b",
)


def validate_hint(hint: str, gold: str) -> None:
    if not hint:
        return
    for pattern in BANNED_HINT_PATTERNS:
        if re.search(pattern, hint, flags=re.IGNORECASE):
            raise ValueError(f"Hint guardrail failed on pattern {pattern!r}: {hint}")

    gold_claim = rf"\b(?:option|choice|letter)\s*\(?{re.escape(gold)}\)?\s*(?:is|works|must|could|valid|true)"
    if re.search(gold_claim, hint, flags=re.IGNORECASE):
        raise ValueError(f"Hint appears to assert the gold letter {gold}: {hint}")


def build_hint(example: Example, level: str) -> str:
    if level == "none":
        return ""
    if level == "generic_hint":
        hint = generic_hint(example)
    elif level == "structured_hint":
        hint = structured_hint(example)
    elif level == "guided_hint":
        hint = guided_hint(example)
    else:
        raise ValueError(f"Unknown hint level: {level}")

    validate_hint(hint, example.gold)
    return hint


def format_label_list(labels: list[str]) -> str:
    if len(labels) == 1:
        return labels[0]
    if len(labels) == 2:
        return f"{labels[0]} or {labels[1]}"
    return ", ".join(labels[:-1]) + f", or {labels[-1]}"


def build_user_prompt(example: Example, level: str) -> tuple[str, str]:
    hint = build_hint(example, level)
    task = "You are solving a multiple-choice logic question."
    if example.dataset == "prontoqa":
        task = "You are solving a true/false logic question with lettered choices."

    prompt = f"{task}\n\n{example.question.strip()}\n"
    if hint:
        prompt += f"\nHint:\n{hint}\n"
    prompt += (
        f"\nYour entire response must be exactly one of these labels: "
        f"{', '.join(example.labels)}. Do not write words or reasoning."
    )
    return prompt, hint


def parse_answer(text: str, labels: list[str]) -> str | None:
    valid = set(labels)
    stripped = text.strip()

    patterns = (
        r"^\s*\(?([A-Z])\)?(?:\s|\.|,|:|\)|$)",
        r"\b(?:answer|option|choice|letter)\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
        r"\(([A-Z])\)",
    )
    for pattern in patterns:
        match = re.search(pattern, stripped, flags=re.IGNORECASE)
        if match:
            letter = match.group(1).upper()
            if letter in valid:
                return letter

    found = [letter.upper() for letter in re.findall(r"\b([A-Z])\b", stripped) if letter.upper() in valid]
    found_unique = unique_in_order(found)
    if len(found_unique) == 1:
        return found_unique[0]
    return None


def stable_seed(base_seed: int, name: str) -> int:
    return base_seed + sum((idx + 1) * ord(ch) for idx, ch in enumerate(name))


def shuffled_examples(examples: list[Example], seed: int, name: str) -> list[Example]:
    items = list(examples)
    rng = random.Random(stable_seed(seed, name))
    rng.shuffle(items)
    return items


def make_result_record(
    example: Example,
    level: str,
    hint: str,
    user_prompt: str,
    raw_text: str,
    elapsed_s: float,
) -> dict[str, Any]:
    parsed = parse_answer(raw_text, example.labels)
    return {
        "dataset": example.dataset,
        "source": example.source,
        "id": example.item_id,
        "hint_level": level,
        "gold": example.gold,
        "parsed": parsed,
        "correct": parsed == example.gold,
        "raw_text": raw_text,
        "elapsed_s": round(elapsed_s, 3),
        "hint": hint,
        "user_prompt": user_prompt,
        "labels": example.labels,
    }


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


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def group_results(records: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for record in records:
        key = f"{record['dataset']}::{record['source']}::{record['id']}"
        grouped.setdefault(key, {})[record["hint_level"]] = record
    return grouped


def qualified_keys(records: list[dict[str, Any]]) -> set[str]:
    grouped = group_results(records)
    keys: set[str] = set()
    for key, by_level in grouped.items():
        none_record = by_level.get("none")
        if not none_record or none_record["correct"]:
            continue
        if any(by_level.get(level, {}).get("correct", False) for level in NON_EMPTY_LEVELS):
            keys.add(key)
    return keys


def count_qualified(records: list[dict[str, Any]], dataset: str) -> int:
    subset = [record for record in records if record["dataset"] == dataset]
    return len(qualified_keys(subset))


def process_examples(
    *,
    examples: list[Example],
    start: int,
    stop: int,
    model: Any,
    tokenizer: Any,
    sampler: Any,
    args: argparse.Namespace,
    raw_path: Path,
    records: list[dict[str, Any]],
    phase_name: str,
) -> None:
    total = min(stop, len(examples))
    for index in range(start, total):
        example = examples[index]
        print(
            f"[{example.dataset}] {phase_name} {index + 1}/{total} "
            f"{example.source}:{example.item_id}",
            flush=True,
        )
        for level in LEVELS:
            user_prompt, hint = build_user_prompt(example, level)
            started = time.perf_counter()
            raw_text = run_generation(model, tokenizer, sampler, user_prompt, args.max_tokens)
            elapsed_s = time.perf_counter() - started
            record = make_result_record(example, level, hint, user_prompt, raw_text, elapsed_s)
            records.append(record)
            append_jsonl(raw_path, record)

        current_qualified = count_qualified(records, example.dataset)
        if args.target_qualified > 0 and current_qualified >= args.target_qualified:
            print(
                f"[{example.dataset}] reached target qualified examples: {current_qualified}",
                flush=True,
            )
            return


def run_dataset(
    *,
    dataset: str,
    primary: list[Example],
    fallback: list[Example],
    model: Any,
    tokenizer: Any,
    sampler: Any,
    args: argparse.Namespace,
    raw_path: Path,
    records: list[dict[str, Any]],
) -> None:
    primary_order = shuffled_examples(primary, args.seed, dataset)
    initial_stop = min(args.max_per_dataset, len(primary_order))
    process_examples(
        examples=primary_order,
        start=0,
        stop=initial_stop,
        model=model,
        tokenizer=tokenizer,
        sampler=sampler,
        args=args,
        raw_path=raw_path,
        records=records,
        phase_name="primary",
    )

    if count_qualified(records, dataset) >= args.target_qualified:
        return

    if count_qualified(records, dataset) < args.min_qualified and args.fallback_max_per_dataset > initial_stop:
        expanded_stop = min(args.fallback_max_per_dataset, len(primary_order))
        if expanded_stop > initial_stop:
            print(
                f"[{dataset}] fewer than {args.min_qualified} qualified examples; "
                f"expanding primary sample to {expanded_stop}.",
                flush=True,
            )
            process_examples(
                examples=primary_order,
                start=initial_stop,
                stop=expanded_stop,
                model=model,
                tokenizer=tokenizer,
                sampler=sampler,
                args=args,
                raw_path=raw_path,
                records=records,
                phase_name="expanded",
            )

    if (
        fallback
        and count_qualified(records, dataset) < args.min_qualified
        and count_qualified(records, dataset) < args.target_qualified
    ):
        fallback_order = shuffled_examples(fallback, args.seed, f"{dataset}_fallback")
        fallback_stop = min(args.fallback_max_per_dataset, len(fallback_order))
        print(
            f"[{dataset}] primary source still has fewer than {args.min_qualified} "
            f"qualified examples; adding fallback source.",
            flush=True,
        )
        process_examples(
            examples=fallback_order,
            start=0,
            stop=fallback_stop,
            model=model,
            tokenizer=tokenizer,
            sampler=sampler,
            args=args,
            raw_path=raw_path,
            records=records,
            phase_name="fallback",
        )


def pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{100.0 * numerator / denominator:.1f}%"


def level_accuracy(records: list[dict[str, Any]], level: str) -> tuple[int, int]:
    subset = [record for record in records if record["hint_level"] == level]
    return sum(1 for record in subset if record["correct"]), len(subset)


def summarize_dataset(dataset: str, records: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    grouped = group_results(records)
    q_keys = qualified_keys(records)
    none_wrong_keys = [
        key
        for key, by_level in grouped.items()
        if by_level.get("none") and not by_level["none"]["correct"]
    ]

    processed = len(grouped)
    lines.append(f"### {dataset}")
    lines.append("")
    lines.append(f"- Processed examples: {processed}")
    lines.append(f"- Qualified examples: {len(q_keys)} ({pct(len(q_keys), processed)})")
    lines.append(f"- None-wrong pool: {len(none_wrong_keys)}")
    lines.append("")
    lines.append("| Hint level | Full-sample accuracy | Qualified-set accuracy | Recovery from none-wrong |")
    lines.append("|---|---:|---:|---:|")

    for level in LEVELS:
        correct, total = level_accuracy(records, level)
        if q_keys:
            q_correct = sum(
                1
                for key in q_keys
                if grouped[key].get(level, {}).get("correct", False)
            )
            q_acc = pct(q_correct, len(q_keys))
        else:
            q_acc = "n/a"

        if level == "none":
            recovery = "n/a"
        else:
            recovered = sum(
                1
                for key in none_wrong_keys
                if grouped[key].get(level, {}).get("correct", False)
            )
            recovery = f"{recovered}/{len(none_wrong_keys)} ({pct(recovered, len(none_wrong_keys))})"

        lines.append(
            f"| `{level}` | {correct}/{total} ({pct(correct, total)}) | "
            f"{q_acc} | {recovery} |"
        )
    lines.append("")

    if q_keys:
        preview = sorted(q_keys)[:10]
        lines.append("Qualified example ids, first 10:")
        for key in preview:
            lines.append(f"- `{key}`")
        lines.append("")

    return lines


def write_summary(path: Path, records: list[dict[str, Any]], args: argparse.Namespace) -> None:
    lines: list[str] = []
    lines.append("# Context Evaluation Summary")
    lines.append("")
    lines.append(f"- Model: `{args.model}`")
    lines.append("- Thinking mode: `enable_thinking=False`")
    lines.append(f"- Seed: `{args.seed}`")
    lines.append(f"- Max tokens per generation: `{args.max_tokens}`")
    lines.append(f"- Target qualified examples per dataset: `{args.target_qualified}`")
    lines.append("")

    by_dataset: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_dataset.setdefault(record["dataset"], []).append(record)

    for dataset in sorted(by_dataset):
        lines.extend(summarize_dataset(dataset, by_dataset[dataset]))

    lines.append("## Prompt Audit")
    lines.append("")
    lines.append(
        "The raw JSONL includes `hint` and `user_prompt` for every call. "
        "Use those fields to spot-check that hints do not directly state the gold letter."
    )
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def load_requested_datasets(names: list[str]) -> dict[str, tuple[list[Example], list[Example]]]:
    if "all" in names:
        names = ["lsat_ar", "bbh_logical_deduction", "prontoqa"]

    loaded: dict[str, tuple[list[Example], list[Example]]] = {}
    for name in names:
        print(f"[data] loading {name}", flush=True)
        if name == "lsat_ar":
            loaded[name] = (load_lsat_ar(), [])
        elif name == "bbh_logical_deduction":
            loaded[name] = load_bbh_primary_and_fallback()
        elif name == "prontoqa":
            loaded[name] = (load_prontoqa(), [])
        else:
            raise ValueError(f"Unknown dataset: {name}")
        primary_count = len(loaded[name][0])
        fallback_count = len(loaded[name][1])
        print(
            f"[data] {name}: primary={primary_count}, fallback={fallback_count}",
            flush=True,
        )
    return loaded


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate precomputed context hints with Qwen non-thinking mode."
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        default=["all"],
        choices=["all", "lsat_ar", "bbh_logical_deduction", "prontoqa"],
        help="Datasets to run.",
    )
    parser.add_argument("--model", default=MODEL_ID, help="mlx_lm model id or local path.")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--max-per-dataset", type=int, default=60)
    parser.add_argument("--fallback-max-per-dataset", type=int, default=120)
    parser.add_argument("--target-qualified", type=int, default=20)
    parser.add_argument("--min-qualified", type=int, default=5)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--results-dir", default="results")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run one example per dataset and do not require qualified examples.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.smoke:
        args.max_per_dataset = 1
        args.fallback_max_per_dataset = 1
        args.target_qualified = 1
        args.min_qualified = 0

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    raw_path = results_dir / "context_eval_raw.jsonl"
    summary_path = results_dir / "context_eval_summary.md"
    raw_path.write_text("", encoding="utf-8")

    datasets = load_requested_datasets(args.datasets)

    print(f"[model] loading {args.model}", flush=True)
    from mlx_lm import load
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(args.model)
    sampler = make_sampler(temp=args.temperature)

    records: list[dict[str, Any]] = []
    for dataset, (primary, fallback) in datasets.items():
        run_dataset(
            dataset=dataset,
            primary=primary,
            fallback=fallback,
            model=model,
            tokenizer=tokenizer,
            sampler=sampler,
            args=args,
            raw_path=raw_path,
            records=records,
        )

    write_summary(summary_path, records, args)
    print(f"[done] wrote {raw_path}", flush=True)
    print(f"[done] wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
