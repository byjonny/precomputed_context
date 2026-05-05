#!/usr/bin/env python3
"""Thinking-exemplar transfer across multiple datasets.

For each dataset:
1. Load one exemplar plus N evaluation examples.
2. Run Qwen with `enable_thinking=True` on the exemplar.
3. Prepend the exemplar question, thinking trace, and answer before each new
   question, then evaluate with `enable_thinking=False`.
4. Compare against a no-context baseline.

Examples keep their native answer format. Multiple-choice datasets use their
original options, while numeric, text, yes/no, and plan-answer datasets are
scored with answer-format-specific parsers.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.parse import urlencode

from run_context_eval import HF_ROWS_ENDPOINT, MODEL_ID, parse_answer, read_url_json


LETTER_LABELS = [chr(ord("A") + idx) for idx in range(10)]
CONDITIONS = ("none", "thinking_exemplar")

MATH_CONFIGS = (
    "algebra",
    "counting_and_probability",
    "geometry",
    "intermediate_algebra",
    "number_theory",
    "prealgebra",
    "precalculus",
)

DEFAULT_DATASETS = (
    "arc_challenge",
    "openbookqa",
    "gsm8k",
    "mmlu_pro",
    "math",
    "svamp",
    "asdiv",
    "aqua",
    "mawps",
    "csqa",
    "strategyqa",
    "bbh_date",
    "bbh_sports",
    "saycan",
    "last_letter",
    "coin_flip",
)


@dataclass(frozen=True)
class ChoiceExample:
    dataset: str
    source: str
    item_id: str
    question: str
    labels: list[str]
    gold: str
    gold_text: str
    metadata: dict[str, Any]
    answer_kind: str = "choice"


def fetch_rows(dataset: str, config: str, split: str, offset: int, length: int) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    current_offset = offset
    remaining = length
    while remaining > 0:
        chunk = min(remaining, 100)
        params = {
            "dataset": dataset,
            "config": config,
            "split": split,
            "offset": current_offset,
            "length": chunk,
        }
        url = f"{HF_ROWS_ENDPOINT}?{urlencode(params)}"
        last_error: Exception | None = None
        for attempt in range(8):
            try:
                data = read_url_json(url)
                break
            except Exception as exc:
                last_error = exc
                sleep_s = min(60, 5 * (attempt + 1))
                print(
                    f"[data] retry {attempt + 1}/8 after fetch error for {dataset}:{config}:{split}: {exc}",
                    flush=True,
                )
                time.sleep(sleep_s)
        else:
            raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error
        page = data.get("rows", [])
        if not page:
            break
        rows.extend((int(item["row_idx"]), item["row"]) for item in page)
        current_offset += len(page)
        remaining -= len(page)
        if len(page) < chunk:
            break
    return rows


def unique_in_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def labels(count: int) -> list[str]:
    return LETTER_LABELS[:count]


def choices_text(choice_labels: Sequence[str], choice_texts: Sequence[str]) -> str:
    return "\n".join(f"({label}) {text}" for label, text in zip(choice_labels, choice_texts, strict=True))


def normalize_answer_text(text: Any) -> str:
    out = str(text).strip()
    out = re.sub(r"^\$+", "", out)
    out = re.sub(r"\s+", " ", out)
    out = out.strip(". ")
    return out


def normalize_for_compare(text: str) -> str:
    text = normalize_answer_text(text).lower()
    text = text.replace(",", "")
    text = re.sub(r"^\$+", "", text)
    text = re.sub(r"\s+", "", text)
    if re.fullmatch(r"-?\d+\.0+", text):
        text = text.split(".", 1)[0]
    return text


def answer_from_gsm8k(answer: str) -> str:
    match = re.search(r"####\s*([-+]?[\d,]+(?:\.\d+)?)", answer)
    if match:
        return match.group(1).replace(",", "")
    numbers = re.findall(r"[-+]?[\d,]+(?:\.\d+)?", answer)
    return numbers[-1].replace(",", "") if numbers else normalize_answer_text(answer)


def extract_boxed(solution: str) -> str:
    start = solution.rfind(r"\boxed{")
    if start == -1:
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", solution)
        return numbers[-1] if numbers else normalize_answer_text(solution[-80:])
    index = start + len(r"\boxed{")
    depth = 1
    chars: list[str] = []
    while index < len(solution) and depth:
        char = solution[index]
        if char == "{":
            depth += 1
            chars.append(char)
        elif char == "}":
            depth -= 1
            if depth:
                chars.append(char)
        else:
            chars.append(char)
        index += 1
    return normalize_answer_text("".join(chars))


def load_choice_answerkey(
    *,
    dataset_name: str,
    source: str,
    dataset_id: str,
    config: str,
    split: str,
    question_field: str,
    offset: int,
    total: int,
) -> list[ChoiceExample]:
    examples: list[ChoiceExample] = []
    for row_idx, row in fetch_rows(dataset_id, config, split, offset, total):
        choice_texts = [str(text).strip() for text in row["choices"]["text"]]
        source_labels = [str(label).strip() for label in row["choices"]["label"]]
        choice_labels = labels(len(choice_texts))
        answer_key = str(row["answerKey"]).strip()
        if answer_key in source_labels:
            gold = choice_labels[source_labels.index(answer_key)]
        elif answer_key in choice_labels:
            gold = answer_key
        else:
            raise ValueError(f"Could not map answerKey {answer_key!r} for {dataset_name}:{row_idx}")
        question = f"Question:\n{str(row[question_field]).strip()}\n\nOptions:\n{choices_text(choice_labels, choice_texts)}"
        examples.append(
            ChoiceExample(
                dataset=dataset_name,
                source=source,
                item_id=str(row.get("id", row_idx)),
                question=question,
                labels=choice_labels,
                gold=gold,
                gold_text=choice_texts[choice_labels.index(gold)],
                metadata={"row_idx": row_idx},
            )
        )
    return examples


def load_arc(offset: int, total: int) -> list[ChoiceExample]:
    return load_choice_answerkey(
        dataset_name="arc_challenge",
        source="allenai/ai2_arc:ARC-Challenge/validation",
        dataset_id="allenai/ai2_arc",
        config="ARC-Challenge",
        split="validation",
        question_field="question",
        offset=offset,
        total=total,
    )


def load_openbookqa(offset: int, total: int) -> list[ChoiceExample]:
    return load_choice_answerkey(
        dataset_name="openbookqa",
        source="allenai/openbookqa:main/validation",
        dataset_id="allenai/openbookqa",
        config="main",
        split="validation",
        question_field="question_stem",
        offset=offset,
        total=total,
    )


def load_gsm8k(offset: int, total: int) -> list[ChoiceExample]:
    rows = fetch_rows("openai/gsm8k", "main", "test", offset, total)
    examples: list[ChoiceExample] = []
    for row_idx, row in rows:
        examples.append(
            ChoiceExample(
                dataset="gsm8k",
                source="openai/gsm8k:main/test",
                item_id=str(row_idx),
                question=f"Question:\n{str(row['question']).strip()}",
                labels=[],
                gold=answer_from_gsm8k(str(row["answer"])),
                gold_text=answer_from_gsm8k(str(row["answer"])),
                metadata={"row_idx": row_idx},
                answer_kind="number",
            )
        )
    return examples


def load_mmlu_pro(offset: int, total: int) -> list[ChoiceExample]:
    examples: list[ChoiceExample] = []
    for row_idx, row in fetch_rows("TIGER-Lab/MMLU-Pro", "default", "test", offset, total):
        choice_texts = [str(option).strip() for option in row["options"]]
        choice_labels = labels(len(choice_texts))
        gold = str(row["answer"]).strip().upper()
        question = (
            f"Question:\n{str(row['question']).strip()}\n\n"
            f"Category: {str(row.get('category', '')).strip()}\n\n"
            f"Options:\n{choices_text(choice_labels, choice_texts)}"
        )
        examples.append(
            ChoiceExample(
                dataset="mmlu_pro",
                source="TIGER-Lab/MMLU-Pro:test",
                item_id=str(row.get("question_id", row_idx)),
                question=question,
                labels=choice_labels,
                gold=gold,
                gold_text=choice_texts[choice_labels.index(gold)],
                metadata={"category": row.get("category", ""), "row_idx": row_idx},
            )
        )
    return examples


def load_math(offset: int, total: int) -> list[ChoiceExample]:
    per_config = max(8, (offset + total + len(MATH_CONFIGS) - 1) // len(MATH_CONFIGS) + 4)
    raw: list[tuple[str, int, dict[str, Any]]] = []
    for config in MATH_CONFIGS:
        for row_idx, row in fetch_rows("EleutherAI/hendrycks_math", config, "test", 0, per_config):
            raw.append((config, row_idx, row))
    raw = raw[offset : offset + total]
    examples: list[ChoiceExample] = []
    for config, row_idx, row in raw:
        answer = extract_boxed(str(row["solution"]))
        examples.append(
            ChoiceExample(
                dataset="math",
                source="EleutherAI/hendrycks_math:test",
                item_id=f"{config}:{row_idx}",
                question=f"Problem:\n{str(row['problem']).strip()}",
                labels=[],
                gold=answer,
                gold_text=answer,
                metadata={"config": config, "level": row.get("level"), "type": row.get("type")},
                answer_kind="text",
            )
        )
    return examples


def load_svamp(offset: int, total: int) -> list[ChoiceExample]:
    rows = fetch_rows("ChilleD/SVAMP", "default", "test", offset, total)
    examples: list[ChoiceExample] = []
    for row_idx, row in rows:
        question = f"Question:\n{str(row.get('question_concat') or (str(row['Body']) + ' ' + str(row['Question']))).strip()}"
        examples.append(
            ChoiceExample(
                dataset="svamp",
                source="ChilleD/SVAMP:test",
                item_id=str(row.get("ID", row_idx)),
                question=question,
                labels=[],
                gold=str(row["Answer"]),
                gold_text=str(row["Answer"]),
                metadata={"row_idx": row_idx, "type": row.get("Type")},
                answer_kind="number",
            )
        )
    return examples


def load_asdiv(offset: int, total: int) -> list[ChoiceExample]:
    rows = fetch_rows("EleutherAI/asdiv", "asdiv", "validation", offset, total)
    examples: list[ChoiceExample] = []
    for row_idx, row in rows:
        match = re.search(r"-?\d+(?:\.\d+)?", str(row["answer"]))
        gold = match.group(0) if match else str(row["answer"])
        question = f"Question:\n{str(row['body']).strip()} {str(row['question']).strip()}"
        examples.append(
            ChoiceExample(
                dataset="asdiv",
                source="EleutherAI/asdiv:validation",
                item_id=str(row_idx),
                question=question,
                labels=[],
                gold=gold,
                gold_text=gold,
                metadata={"solution_type": row.get("solution_type"), "formula": row.get("formula")},
                answer_kind="number",
            )
        )
    return examples


def load_aqua(offset: int, total: int) -> list[ChoiceExample]:
    examples: list[ChoiceExample] = []
    for row_idx, row in fetch_rows("deepmind/aqua_rat", "raw", "test", offset, total):
        option_pairs: list[tuple[str, str]] = []
        for option in row["options"]:
            match = re.match(r"\s*([A-E])\)\s*(.*)", str(option).strip())
            if match:
                option_pairs.append((match.group(1), match.group(2).strip()))
        choice_labels = [label for label, _ in option_pairs]
        choice_texts = [text for _, text in option_pairs]
        gold = str(row["correct"]).strip().upper()
        question = f"Question:\n{str(row['question']).strip()}\n\nOptions:\n{choices_text(choice_labels, choice_texts)}"
        examples.append(
            ChoiceExample(
                dataset="aqua",
                source="deepmind/aqua_rat:raw/test",
                item_id=str(row_idx),
                question=question,
                labels=choice_labels,
                gold=gold,
                gold_text=choice_texts[choice_labels.index(gold)],
                metadata={"row_idx": row_idx},
            )
        )
    return examples


def load_mawps(offset: int, total: int) -> list[ChoiceExample]:
    rows = fetch_rows("MU-NLPC/Calc-mawps", "default", "test", offset, total)
    examples: list[ChoiceExample] = []
    for row_idx, row in rows:
        examples.append(
            ChoiceExample(
                dataset="mawps",
                source="MU-NLPC/Calc-mawps:test",
                item_id=str(row.get("id", row_idx)),
                question=f"Question:\n{str(row['question']).strip()}",
                labels=[],
                gold=str(row["result"]),
                gold_text=str(row["result"]),
                metadata={"row_idx": row_idx},
                answer_kind="number",
            )
        )
    return examples


def load_csqa(offset: int, total: int) -> list[ChoiceExample]:
    return load_choice_answerkey(
        dataset_name="csqa",
        source="tau/commonsense_qa:validation",
        dataset_id="tau/commonsense_qa",
        config="default",
        split="validation",
        question_field="question",
        offset=offset,
        total=total,
    )


def load_strategyqa(offset: int, total: int) -> list[ChoiceExample]:
    examples: list[ChoiceExample] = []
    for row_idx, row in fetch_rows("ChilleD/StrategyQA", "default", "test", offset, total):
        gold = "Yes" if bool(row["answer"]) else "No"
        question = f"Question:\n{str(row['question']).strip()}"
        examples.append(
            ChoiceExample(
                dataset="strategyqa",
                source="ChilleD/StrategyQA:test",
                item_id=str(row.get("qid", row_idx)),
                question=question,
                labels=[],
                gold=gold,
                gold_text=gold,
                metadata={"row_idx": row_idx, "term": row.get("term")},
                answer_kind="yesno",
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


def load_bbh_date(offset: int, total: int) -> list[ChoiceExample]:
    examples: list[ChoiceExample] = []
    for row_idx, row in fetch_rows("lukaemon/bbh", "date_understanding", "test", offset, total):
        question = str(row["input"]).strip()
        choice_labels = unique_in_order(re.findall(r"\(([A-Z])\)", question))
        gold = parse_bbh_target(str(row["target"]))
        examples.append(
            ChoiceExample(
                dataset="bbh_date",
                source="lukaemon/bbh:date_understanding/test",
                item_id=str(row_idx),
                question=question,
                labels=choice_labels,
                gold=gold,
                gold_text=gold,
                metadata={"row_idx": row_idx},
            )
        )
    return examples


def load_bbh_sports(offset: int, total: int) -> list[ChoiceExample]:
    examples: list[ChoiceExample] = []
    for row_idx, row in fetch_rows("lukaemon/bbh", "sports_understanding", "test", offset, total):
        target = str(row["target"]).strip().lower()
        gold = "Yes" if target == "yes" else "No"
        question = str(row["input"]).strip()
        examples.append(
            ChoiceExample(
                dataset="bbh_sports",
                source="lukaemon/bbh:sports_understanding/test",
                item_id=str(row_idx),
                question=question,
                labels=[],
                gold=gold,
                gold_text=gold,
                metadata={"row_idx": row_idx},
                answer_kind="yesno",
            )
        )
    return examples


def load_saycan(offset: int, total: int) -> list[ChoiceExample]:
    rows = fetch_rows("chiayewken/saycan", "default", "test", offset, total)
    examples: list[ChoiceExample] = []
    for row_idx, row in rows:
        examples.append(
            ChoiceExample(
                dataset="saycan",
                source="chiayewken/saycan:test",
                item_id=str(row_idx),
                question=f"Instruction:\n{str(row['INPUT']).strip()}\n\nWrite the plan to execute.",
                labels=[],
                gold=str(row["OUTPUT"]).strip(),
                gold_text=str(row["OUTPUT"]).strip(),
                metadata={"row_idx": row_idx},
                answer_kind="plan",
            )
        )
    return examples


def load_last_letter(offset: int, total: int) -> list[ChoiceExample]:
    rows = fetch_rows("ChilleD/LastLetterConcat", "default", "test", offset, total)
    examples: list[ChoiceExample] = []
    for row_idx, row in rows:
        examples.append(
            ChoiceExample(
                dataset="last_letter",
                source="ChilleD/LastLetterConcat:test",
                item_id=str(row_idx),
                question=f"Question:\n{str(row['question']).strip()}",
                labels=[],
                gold=str(row["answer"]).strip(),
                gold_text=str(row["answer"]).strip(),
                metadata={"row_idx": row_idx},
                answer_kind="text",
            )
        )
    return examples


def load_coin_flip(offset: int, total: int) -> list[ChoiceExample]:
    examples: list[ChoiceExample] = []
    for row_idx, row in fetch_rows("skrishna/coin_flip", "default", "test", offset, total):
        target = str(row["targets"]).strip().lower()
        gold = "Yes" if target == "yes" else "No"
        question = str(row["inputs"]).strip()
        examples.append(
            ChoiceExample(
                dataset="coin_flip",
                source="skrishna/coin_flip:test",
                item_id=str(row_idx),
                question=question,
                labels=[],
                gold=gold,
                gold_text=gold,
                metadata={"row_idx": row_idx},
                answer_kind="yesno",
            )
        )
    return examples


LOADERS = {
    "arc_challenge": load_arc,
    "openbookqa": load_openbookqa,
    "gsm8k": load_gsm8k,
    "mmlu_pro": load_mmlu_pro,
    "math": load_math,
    "svamp": load_svamp,
    "asdiv": load_asdiv,
    "aqua": load_aqua,
    "mawps": load_mawps,
    "csqa": load_csqa,
    "strategyqa": load_strategyqa,
    "bbh_date": load_bbh_date,
    "bbh_sports": load_bbh_sports,
    "saycan": load_saycan,
    "last_letter": load_last_letter,
    "coin_flip": load_coin_flip,
}


def load_dataset_examples(dataset: str, exemplar_offset: int, eval_offset: int, limit: int) -> tuple[ChoiceExample, list[ChoiceExample]]:
    loader = LOADERS[dataset]
    start = min(exemplar_offset, eval_offset)
    total = max(exemplar_offset, eval_offset + limit) - start
    loaded = loader(start, total)
    by_row = {idx + start: example for idx, example in enumerate(loaded)}
    exemplar = by_row[exemplar_offset]
    eval_examples = [by_row[offset] for offset in range(eval_offset, eval_offset + limit)]
    eval_examples = [example for example in eval_examples if example.item_id != exemplar.item_id]
    return exemplar, eval_examples[:limit]


def build_exemplar_prompt(example: ChoiceExample) -> str:
    instruction = final_answer_instruction(example, final_line=True)
    return (
        f"You are solving a {example.dataset} problem.\n"
        "Write the complete reasoning, but keep it concise. The very last line "
        f"must follow this format: `{instruction}`.\n\n"
        f"{example.question.strip()}\n"
    )


def final_answer_instruction(example: ChoiceExample, *, final_line: bool = False) -> str:
    if example.answer_kind == "choice":
        labels_text = ", ".join(example.labels)
        return "Final answer: <letter>" if final_line else f"exactly one of these labels: {labels_text}"
    if example.answer_kind == "yesno":
        return "Final answer: <Yes or No>" if final_line else "exactly Yes or No"
    if example.answer_kind == "number":
        return "Final answer: <number>" if final_line else "the numeric answer only"
    if example.answer_kind == "plan":
        return "Final answer: <plan>" if final_line else "the plan text only"
    return "Final answer: <answer>" if final_line else "the answer only"


def build_eval_prompt(
    example: ChoiceExample,
    *,
    condition: str,
    exemplar: ChoiceExample,
    exemplar_thinking: str,
    exemplar_answer_text: str,
) -> str:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    prefix = f"You are solving a {example.dataset} problem.\n\n"
    if condition == "thinking_exemplar":
        prefix += (
            "Below is one solved example from the same dataset. Use it as a "
            "transferable reasoning pattern, but do not copy its answer for the new problem.\n\n"
            "Solved example question:\n"
            f"{exemplar.question.strip()}\n\n"
            "Solved example thinking trace:\n"
            f"{exemplar_thinking.strip()}\n\n"
            "Solved example final answer:\n"
            f"{exemplar_answer_text.strip()}\n\n"
            "Now answer the new problem.\n\n"
        )
    return (
        f"{prefix}{example.question.strip()}\n\n"
        "Your entire response must be "
        f"{final_answer_instruction(example)}. Do not write words or reasoning."
    )


def system_message_for(*, enable_thinking: bool, answer_kind: str) -> str:
    if enable_thinking:
        return "Output the requested answer format exactly."
    if answer_kind == "choice":
        return "Output exactly one capital letter for the selected choice. Nothing else."
    if answer_kind == "yesno":
        return "Output exactly Yes or No. Nothing else."
    if answer_kind == "number":
        return "Output exactly the numeric answer. Nothing else."
    return "Output exactly the final answer text. Nothing else."


def apply_chat_template(tokenizer: Any, user_prompt: str, *, enable_thinking: bool, answer_kind: str) -> str:
    system = system_message_for(enable_thinking=enable_thinking, answer_kind=answer_kind)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}]
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
    answer_kind: str,
    max_tokens: int,
) -> str:
    from mlx_lm import generate

    prompt = apply_chat_template(tokenizer, user_prompt, enable_thinking=enable_thinking, answer_kind=answer_kind)
    return generate(
        model,
        tokenizer,
        prompt=prompt,
        max_tokens=max_tokens,
        sampler=sampler,
        verbose=False,
    )


def eval_max_tokens(example: ChoiceExample, default_max_tokens: int) -> int:
    if example.answer_kind == "choice":
        return min(default_max_tokens, 16)
    if example.answer_kind in {"yesno", "number", "text"}:
        return max(default_max_tokens, 64)
    if example.answer_kind == "plan":
        return max(default_max_tokens, 256)
    return default_max_tokens


def final_answer_region(text: str) -> str:
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    matches = list(re.finditer(r"\bfinal\s+answer\s*(?:is|:)?\s*", text, flags=re.IGNORECASE))
    if matches:
        return text[matches[-1].end() :].strip()
    return text.strip()


def parse_yesno(text: str) -> str | None:
    region = final_answer_region(text)
    matches = re.findall(r"\b(yes|no)\b", region, flags=re.IGNORECASE)
    if not matches:
        matches = re.findall(r"\b(yes|no)\b", text, flags=re.IGNORECASE)
    return matches[-1].capitalize() if matches else None


def parse_number(text: str) -> str | None:
    region = final_answer_region(text)
    matches = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", region)
    if not matches:
        matches = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    return matches[-1].replace(",", "") if matches else None


def parse_text_answer(text: str) -> str | None:
    region = final_answer_region(text)
    if not region:
        return None
    return region.strip().strip("`").strip()


def parse_model_answer(text: str, example: ChoiceExample) -> str | None:
    if example.answer_kind == "choice":
        return parse_answer(text, example.labels)
    if example.answer_kind == "yesno":
        return parse_yesno(text)
    if example.answer_kind == "number":
        return parse_number(text)
    return parse_text_answer(text)


def answers_match(parsed: str | None, example: ChoiceExample) -> bool:
    if parsed is None:
        return False
    if example.answer_kind == "choice":
        return parsed == example.gold
    if example.answer_kind == "yesno":
        return parsed.lower() == example.gold.lower()
    if example.answer_kind == "number":
        return normalize_for_compare(parsed) == normalize_for_compare(example.gold)
    if example.answer_kind == "plan":
        return normalize_plan(parsed) == normalize_plan(example.gold)
    return normalize_for_compare(parsed) == normalize_for_compare(example.gold)


def normalize_plan(text: str) -> str:
    text = normalize_answer_text(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_final_answer(text: str, example: ChoiceExample) -> str | None:
    if example.answer_kind != "choice":
        return parse_model_answer(text, example)
    valid = set(example.labels)
    for pattern in (
        r"\bfinal\s+answer\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
        r"\banswer\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
        r"\boption\s*(?:is|:)?\s*\(?([A-Z])\)?\b",
    ):
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for letter in reversed(matches):
            letter = letter.upper()
            if letter in valid:
                return letter
    if "</think>" in text:
        parsed = parse_answer(text.rsplit("</think>", 1)[1], example.labels)
        if parsed:
            return parsed
    letters = [letter.upper() for letter in re.findall(r"\b([A-Z])\b", text) if letter.upper() in valid]
    return letters[-1] if letters else None


def split_thinking_output(text: str, example: ChoiceExample, parsed_answer: str | None = None) -> tuple[str, str]:
    canonical = f"Final answer: {parsed_answer}" if parsed_answer else ""
    if "<think>" in text and "</think>" in text:
        thinking = text.split("<think>", 1)[1].split("</think>", 1)[0].strip()
        answer_text = text.rsplit("</think>", 1)[1].strip()
        if parsed_answer and not re.search(r"\bfinal\s+answer\b", answer_text, flags=re.IGNORECASE):
            answer_text = canonical
        return thinking, answer_text
    if "</think>" in text:
        thinking, answer_text = text.split("</think>", 1)
        thinking = thinking.replace("<think>", "").strip()
        if parsed_answer and not re.search(r"\bfinal\s+answer\b", answer_text, flags=re.IGNORECASE):
            answer_text = canonical
        return thinking, answer_text.strip()
    final_match = re.search(r"\bfinal\s+answer\s*(?:is|:)?\s*\(?([A-Z])\)?\b", text, flags=re.IGNORECASE)
    if final_match:
        return text[: final_match.start()].strip(), text[final_match.start() :].strip()
    if parsed_answer:
        return text.strip(), canonical
    return text.strip(), text.strip()


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def example_record(example: ChoiceExample) -> dict[str, Any]:
    return {
        "dataset": example.dataset,
        "source": example.source,
        "id": example.item_id,
        "question": example.question,
        "labels": example.labels,
        "gold": example.gold,
        "gold_text": example.gold_text,
        "answer_kind": example.answer_kind,
        "metadata": example.metadata,
    }


def make_eval_record(
    *,
    run_id: str,
    example: ChoiceExample,
    condition: str,
    user_prompt: str,
    raw_text: str,
    elapsed_s: float,
) -> dict[str, Any]:
    parsed = parse_model_answer(raw_text, example)
    return {
        "run_id": run_id,
        **example_record(example),
        "condition": condition,
        "parsed": parsed,
        "correct": answers_match(parsed, example),
        "raw_text": raw_text,
        "elapsed_s": round(elapsed_s, 3),
        "user_prompt": user_prompt,
    }


def compute_stats(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_dataset_condition: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    by_dataset_id: dict[tuple[str, str], dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        by_dataset_condition[(record["dataset"], record["condition"])].append(record)
        by_dataset_id[(record["dataset"], record["id"])][record["condition"]] = record
    out: dict[str, dict[str, Any]] = {}
    for dataset in sorted({record["dataset"] for record in records}):
        row: dict[str, Any] = {"recovered": [], "harmed": []}
        for condition in CONDITIONS:
            condition_rows = by_dataset_condition.get((dataset, condition), [])
            correct = sum(1 for item in condition_rows if item["correct"])
            row[condition] = {
                "correct": correct,
                "total": len(condition_rows),
                "accuracy": correct / len(condition_rows) if condition_rows else 0.0,
            }
        for (ds, _), conds in by_dataset_id.items():
            if ds != dataset or not all(condition in conds for condition in CONDITIONS):
                continue
            none = conds["none"]
            ctx = conds["thinking_exemplar"]
            if not none["correct"] and ctx["correct"]:
                row["recovered"].append(str(none["id"]))
            if none["correct"] and not ctx["correct"]:
                row["harmed"].append(str(none["id"]))
        row["delta_correct"] = row["thinking_exemplar"]["correct"] - row["none"]["correct"]
        row["delta_accuracy"] = row["thinking_exemplar"]["accuracy"] - row["none"]["accuracy"]
        out[dataset] = row
    return out


def write_csv(path: Path, stats: dict[str, dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["dataset", "none_correct", "none_total", "none_accuracy", "context_correct", "context_total", "context_accuracy", "delta_correct", "delta_accuracy", "recovered", "harmed"])
        for dataset in DEFAULT_DATASETS:
            if dataset not in stats:
                continue
            row = stats[dataset]
            writer.writerow(
                [
                    dataset,
                    row["none"]["correct"],
                    row["none"]["total"],
                    f"{row['none']['accuracy']:.6f}",
                    row["thinking_exemplar"]["correct"],
                    row["thinking_exemplar"]["total"],
                    f"{row['thinking_exemplar']['accuracy']:.6f}",
                    row["delta_correct"],
                    f"{row['delta_accuracy']:.6f}",
                    " ".join(row["recovered"]),
                    " ".join(row["harmed"]),
                ]
            )


def write_chart_svg(path: Path, stats: dict[str, dict[str, Any]]) -> None:
    datasets = [dataset for dataset in DEFAULT_DATASETS if dataset in stats]
    totals = sorted({stats[dataset]["none"]["total"] for dataset in datasets})
    if not totals:
        sample_note = "no evaluation examples"
    elif len(totals) == 1:
        sample_note = f"{totals[0]} evaluation examples per dataset"
    else:
        sample_note = f"{min(totals)}-{max(totals)} evaluation examples per dataset"
    width = 1180
    row_h = 34
    left = 250
    chart_w = 760
    top = 55
    height = top + row_h * len(datasets) + 60
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="20" y="30" font-family="Arial" font-size="20" font-weight="700">Thinking Exemplar Transfer Accuracy</text>',
        f'<text x="20" y="50" font-family="Arial" font-size="12" fill="#555">Qwen/Qwen3.5-4B, non-thinking evaluation, {html.escape(sample_note)}</text>',
    ]
    for pct in range(0, 101, 25):
        x = left + chart_w * pct / 100
        lines.append(f'<line x1="{x:.1f}" y1="{top-10}" x2="{x:.1f}" y2="{height-40}" stroke="#e5e7eb" stroke-width="1"/>')
        lines.append(f'<text x="{x-8:.1f}" y="{height-20}" font-family="Arial" font-size="11" fill="#555">{pct}%</text>')
    for idx, dataset in enumerate(datasets):
        y = top + idx * row_h
        none_acc = stats[dataset]["none"]["accuracy"] * 100
        ctx_acc = stats[dataset]["thinking_exemplar"]["accuracy"] * 100
        none_w = chart_w * none_acc / 100
        ctx_w = chart_w * ctx_acc / 100
        lines.append(f'<text x="20" y="{y+18}" font-family="Arial" font-size="12">{html.escape(dataset)}</text>')
        lines.append(f'<rect x="{left}" y="{y+4}" width="{none_w:.1f}" height="10" fill="#64748b"/>')
        lines.append(f'<rect x="{left}" y="{y+18}" width="{ctx_w:.1f}" height="10" fill="#2563eb"/>')
        lines.append(f'<text x="{left+chart_w+12}" y="{y+13}" font-family="Arial" font-size="11" fill="#334155">none {none_acc:.1f}%</text>')
        lines.append(f'<text x="{left+chart_w+12}" y="{y+27}" font-family="Arial" font-size="11" fill="#1d4ed8">ctx {ctx_acc:.1f}%</text>')
    lines.append('<rect x="20" y="{0}" width="12" height="12" fill="#64748b"/>'.format(height - 45))
    lines.append('<text x="38" y="{0}" font-family="Arial" font-size="12" fill="#334155">none</text>'.format(height - 35))
    lines.append('<rect x="90" y="{0}" width="12" height="12" fill="#2563eb"/>'.format(height - 45))
    lines.append('<text x="108" y="{0}" font-family="Arial" font-size="12" fill="#1d4ed8">thinking_exemplar</text>'.format(height - 35))
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(
    path: Path,
    *,
    run_id: str,
    args: argparse.Namespace,
    stats: dict[str, dict[str, Any]],
    raw_path: Path,
    exemplar_path: Path,
    csv_path: Path,
    chart_path: Path,
) -> None:
    lines = [
        "# Multi-Dataset Thinking-Exemplar Transfer",
        "",
        f"- Run id: `{run_id}`",
        f"- Model: `{args.model}`",
        "- Exemplar generation: `enable_thinking=True`",
        "- Evaluation generation: `enable_thinking=False`",
        f"- Eval examples per dataset: `{args.limit}`",
        f"- Thinking max tokens: `{args.thinking_max_tokens}`",
        "",
        "## Results",
        "",
        "| Dataset | None | Thinking exemplar | Delta | Recovered | Harmed |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    total_none_correct = total_ctx_correct = total = 0
    for dataset in DEFAULT_DATASETS:
        if dataset not in stats:
            continue
        row = stats[dataset]
        none = row["none"]
        ctx = row["thinking_exemplar"]
        total_none_correct += none["correct"]
        total_ctx_correct += ctx["correct"]
        total += none["total"]
        lines.append(
            f"| `{dataset}` | {none['correct']}/{none['total']} ({none['accuracy']:.1%}) | "
            f"{ctx['correct']}/{ctx['total']} ({ctx['accuracy']:.1%}) | "
            f"{row['delta_correct']:+d} ({row['delta_accuracy']:+.1%}) | "
            f"{len(row['recovered'])} | {len(row['harmed'])} |"
        )
    if total:
        lines.append(
            f"| **Total** | **{total_none_correct}/{total} ({total_none_correct/total:.1%})** | "
            f"**{total_ctx_correct}/{total} ({total_ctx_correct/total:.1%})** | "
            f"**{total_ctx_correct-total_none_correct:+d} ({(total_ctx_correct-total_none_correct)/total:+.1%})** |  |  |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Exemplar JSONL: `{exemplar_path}`",
            f"- Raw eval JSONL: `{raw_path}`",
            f"- CSV table: `{csv_path}`",
            f"- SVG chart: `{chart_path}`",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run thinking-exemplar transfer on many datasets.")
    parser.add_argument("--datasets", nargs="+", default=list(DEFAULT_DATASETS), choices=list(DEFAULT_DATASETS))
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--exemplar-offset", type=int, default=0)
    parser.add_argument("--eval-offset", type=int, default=1)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--thinking-max-tokens", type=int, default=4096)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--results-dir", default="results/thinking_exemplar_multi")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or f"thinking_exemplar_multi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    raw_path = results_dir / f"{run_id}.jsonl"
    exemplar_path = results_dir / f"{run_id}_exemplars.jsonl"
    summary_path = results_dir / f"{run_id}.md"
    csv_path = results_dir / f"{run_id}.csv"
    chart_path = results_dir / f"{run_id}_chart.svg"

    print(f"[data] loading {len(args.datasets)} datasets", flush=True)
    dataset_examples: dict[str, tuple[ChoiceExample, list[ChoiceExample]]] = {}
    for dataset in args.datasets:
        exemplar, eval_examples = load_dataset_examples(dataset, args.exemplar_offset, args.eval_offset, args.limit)
        dataset_examples[dataset] = (exemplar, eval_examples)
        print(f"[data] {dataset}: exemplar={exemplar.item_id}, eval={len(eval_examples)}", flush=True)

    if args.dry_run:
        for dataset, (exemplar, eval_examples) in dataset_examples.items():
            fake_answer = f"Final answer: {exemplar.gold if exemplar.answer_kind == 'choice' else exemplar.gold_text}"
            print(f"\n===== {dataset} exemplar =====\n{build_exemplar_prompt(exemplar)[:4000]}")
            print(f"\n===== {dataset} eval none =====\n{build_eval_prompt(eval_examples[0], condition='none', exemplar=exemplar, exemplar_thinking='...', exemplar_answer_text=fake_answer)[:4000]}")
            print(f"\n===== {dataset} eval context =====\n{build_eval_prompt(eval_examples[0], condition='thinking_exemplar', exemplar=exemplar, exemplar_thinking='...', exemplar_answer_text=fake_answer)[:4000]}")
        return 0

    print(f"[model] loading {args.model}", flush=True)
    from mlx_lm import load
    from mlx_lm.sample_utils import make_sampler

    model, tokenizer = load(args.model)
    sampler = make_sampler(temp=args.temperature)

    raw_path.write_text("", encoding="utf-8")
    exemplar_path.write_text("", encoding="utf-8")
    records: list[dict[str, Any]] = []
    exemplars: dict[str, dict[str, Any]] = {}

    for dataset, (exemplar, eval_examples) in dataset_examples.items():
        print(f"[exemplar] {dataset} row={exemplar.item_id}", flush=True)
        exemplar_prompt = build_exemplar_prompt(exemplar)
        started = time.perf_counter()
        raw_text = run_generation(
            model,
            tokenizer,
            sampler,
            exemplar_prompt,
            enable_thinking=True,
            answer_kind=exemplar.answer_kind,
            max_tokens=args.thinking_max_tokens,
        )
        elapsed_s = time.perf_counter() - started
        parsed_answer = parse_final_answer(raw_text, exemplar)
        thinking, answer_text = split_thinking_output(raw_text, exemplar, parsed_answer)
        exemplar_record = {
            "run_id": run_id,
            **example_record(exemplar),
            "thinking_prompt": exemplar_prompt,
            "raw_text": raw_text,
            "thinking": thinking,
            "answer_text": answer_text,
            "parsed_answer": parsed_answer,
            "correct": answers_match(parsed_answer, exemplar),
            "elapsed_s": round(elapsed_s, 3),
            "enable_thinking": True,
        }
        exemplars[dataset] = exemplar_record
        append_jsonl(exemplar_path, exemplar_record)

        for index, example in enumerate(eval_examples, start=1):
            print(f"[eval] {dataset} {index}/{len(eval_examples)} row={example.item_id}", flush=True)
            for condition in CONDITIONS:
                user_prompt = build_eval_prompt(
                    example,
                    condition=condition,
                    exemplar=exemplar,
                    exemplar_thinking=thinking,
                    exemplar_answer_text=answer_text,
                )
                started = time.perf_counter()
                raw_output = run_generation(
                    model,
                    tokenizer,
                    sampler,
                    user_prompt,
                    enable_thinking=False,
                    answer_kind=example.answer_kind,
                    max_tokens=eval_max_tokens(example, args.max_tokens),
                )
                elapsed = time.perf_counter() - started
                record = make_eval_record(
                    run_id=run_id,
                    example=example,
                    condition=condition,
                    user_prompt=user_prompt,
                    raw_text=raw_output,
                    elapsed_s=elapsed,
                )
                records.append(record)
                append_jsonl(raw_path, record)

    st = compute_stats(records)
    write_csv(csv_path, st)
    write_chart_svg(chart_path, st)
    write_summary(
        summary_path,
        run_id=run_id,
        args=args,
        stats=st,
        raw_path=raw_path,
        exemplar_path=exemplar_path,
        csv_path=csv_path,
        chart_path=chart_path,
    )
    print(f"[done] wrote {summary_path}", flush=True)
    print(f"[done] wrote {csv_path}", flush=True)
    print(f"[done] wrote {chart_path}", flush=True)
    print(f"[done] wrote {raw_path}", flush=True)
    print(f"[done] wrote {exemplar_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
