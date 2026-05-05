#!/usr/bin/env python3
"""Evaluate transfer-only structured hints across multiple reasoning datasets.

The structured hints in this script are intentionally weaker than a solver:
they expose a reusable task template plus question-text structure, but they do
not compute final states, target candidates, proof chains, or answer letters.
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
from typing import Any

from run_context_eval import (
    HF_ROWS_ENDPOINT,
    MODEL_ID,
    Example,
    labels_from_text,
    load_lsat_ar,
    load_prontoqa,
    parse_answer,
    parse_bbh_target,
    read_url_json,
    split_sentences,
    trim,
    unique_in_order,
    validate_hint,
)
from urllib.parse import urlencode


LEVELS = ["none", "structured"]


DATASET_INFO = {
    "bbh_logical_five": {
        "source": "lukaemon/bbh:logical_deduction_five_objects",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "Earlier BBH logical-deduction examples used for v1/v6 transfer templates.",
    },
    "bbh_logical_seven": {
        "source": "lukaemon/bbh:logical_deduction_seven_objects",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "Earlier BBH logical-deduction examples used for v1/v6 transfer templates.",
    },
    "bbh_tracking_five": {
        "source": "lukaemon/bbh:tracking_shuffled_objects_five_objects",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few shuffled-object examples: initialize holder table, apply swaps in order.",
    },
    "bbh_tracking_seven": {
        "source": "lukaemon/bbh:tracking_shuffled_objects_seven_objects",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "Same shuffled-object table template transferred to seven-object cases.",
    },
    "bbh_web_lies": {
        "source": "lukaemon/bbh:web_of_lies",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few truth-chain examples: evaluate speaker claims in sentence order.",
    },
    "bbh_date": {
        "source": "lukaemon/bbh:date_understanding",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few date-understanding examples: identify anchor date, requested offset, and output format.",
    },
    "bbh_temporal": {
        "source": "lukaemon/bbh:temporal_sequences",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few temporal-sequence examples: mark occupied time intervals and compare options to the free interval.",
    },
    "bbh_disambiguation": {
        "source": "lukaemon/bbh:disambiguation_qa",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few pronoun-disambiguation examples: isolate pronoun, candidate antecedents, and ambiguity option.",
    },
    "bbh_colored_objects": {
        "source": "lukaemon/bbh:reasoning_about_colored_objects",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few colored-object examples: inventory objects, apply removal/filter, then count requested attribute.",
    },
    "bbh_penguins": {
        "source": "lukaemon/bbh:penguins_in_a_table",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few table-query examples: isolate relevant table, added row, target column, and option map.",
    },
    "bbh_navigate": {
        "source": "lukaemon/bbh:navigate",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few navigation examples: update a 2D displacement table and test return-to-start.",
    },
    "bbh_formal_fallacies": {
        "source": "lukaemon/bbh:formal_fallacies",
        "url": "https://huggingface.co/datasets/lukaemon/bbh",
        "template_seed": "First few formal-fallacy examples: separate premises from conclusion and check entailment direction.",
    },
    "reclor": {
        "source": "hadithya369/ReClor:validation",
        "url": "https://huggingface.co/datasets/hadithya369/ReClor",
        "template_seed": "First few ReClor logical-reading examples: separate argument, question task, and answer-choice roles.",
    },
    "logiqa": {
        "source": "lucasmccabe/logiqa:validation",
        "url": "https://huggingface.co/datasets/lucasmccabe/logiqa",
        "template_seed": "First few LogiQA examples: separate argument text, question task, and answer-choice roles.",
    },
    "qasc": {
        "source": "allenai/qasc:validation",
        "url": "https://huggingface.co/datasets/allenai/qasc",
        "template_seed": "First few QASC examples: identify asked concept/property and compare choices using question text only.",
    },
    "openbookqa": {
        "source": "allenai/openbookqa:main/validation",
        "url": "https://huggingface.co/datasets/allenai/openbookqa",
        "template_seed": "First few OpenBookQA examples: identify science relation in the question and eliminate implausible choices.",
    },
    "arc_challenge": {
        "source": "allenai/ai2_arc:ARC-Challenge/validation",
        "url": "https://huggingface.co/datasets/allenai/ai2_arc",
        "template_seed": "First few ARC-Challenge examples: classify the science question type and compare choices to the asked property.",
    },
    "hellaswag": {
        "source": "Rowan/hellaswag:validation",
        "url": "https://huggingface.co/datasets/Rowan/hellaswag",
        "template_seed": "First few HellaSwag examples: preserve event participants, action continuity, and physical plausibility.",
    },
    "winogrande": {
        "source": "allenai/winogrande:winogrande_debiased/validation",
        "url": "https://huggingface.co/datasets/allenai/winogrande",
        "template_seed": "First few WinoGrande examples: compare candidate fillers by semantic role in the sentence.",
    },
    "proofwriter": {
        "source": "tasksource/proofwriter:validation",
        "url": "https://huggingface.co/datasets/tasksource/proofwriter",
        "template_seed": "First few ProofWriter examples: forward-chain from facts and rules to the queried statement.",
    },
    "prontoqa": {
        "source": "renma/ProntoQA:dev_gpt4",
        "url": "https://huggingface.co/datasets/renma/ProntoQA",
        "template_seed": "Earlier ProntoQA hint-lab cases: forward-chain from subject facts to query predicate.",
    },
    "lsat_ar": {
        "source": "hails/agieval-lsat-ar:test",
        "url": "https://huggingface.co/datasets/hails/agieval-lsat-ar",
        "template_seed": "Earlier LSAT-AR examples: setup/rules/focus decomposition before checking choices.",
    },
}


def fetch_hf_rows_window(dataset: str, config: str, split: str, offset: int, length: int) -> list[tuple[int, dict[str, Any]]]:
    params = {
        "dataset": dataset,
        "config": config,
        "split": split,
        "offset": offset,
        "length": length,
    }
    data = read_url_json(f"{HF_ROWS_ENDPOINT}?{urlencode(params)}")
    return [(int(item["row_idx"]), item["row"]) for item in data.get("rows", [])]


def load_bbh_mc(config: str, dataset_name: str, source: str, offset: int, limit: int) -> list[Example]:
    examples: list[Example] = []
    for row_idx, row in fetch_hf_rows_window("lukaemon/bbh", config, "test", offset, limit):
        question = str(row["input"]).strip()
        labels = labels_from_text(question, default_count=7)
        examples.append(
            Example(
                dataset=dataset_name,
                source=source,
                item_id=str(row_idx),
                question=question,
                labels=labels,
                gold=parse_bbh_target(str(row["target"])),
                metadata={"config": config},
            )
        )
    return examples


def load_bbh_web_of_lies(offset: int, limit: int) -> list[Example]:
    examples: list[Example] = []
    for row_idx, row in fetch_hf_rows_window("lukaemon/bbh", "web_of_lies", "test", offset, limit):
        target = str(row["target"]).strip().lower()
        if target not in {"yes", "no"}:
            raise ValueError(f"Unexpected web_of_lies target: {row['target']!r}")
        question = f"{str(row['input']).strip()}\nOptions:\n(A) Yes\n(B) No"
        examples.append(
            Example(
                dataset="bbh_web_lies",
                source="bbh_web_of_lies",
                item_id=str(row_idx),
                question=question,
                labels=["A", "B"],
                gold="A" if target == "yes" else "B",
                metadata={"target_text": row["target"]},
            )
        )
    return examples


def relabel_dash_options(question: str, pairs: list[tuple[str, str]]) -> str:
    if "Options:" in question:
        question = question.split("Options:", 1)[0].rstrip()
    options = "\n".join(f"({label}) {text}" for label, text in pairs)
    return f"{question}\nOptions:\n{options}"


def load_bbh_binary(
    config: str,
    dataset_name: str,
    source: str,
    offset: int,
    limit: int,
    option_pairs: list[tuple[str, str]],
) -> list[Example]:
    examples: list[Example] = []
    target_map = {text.lower(): label for label, text in option_pairs}
    for row_idx, row in fetch_hf_rows_window("lukaemon/bbh", config, "test", offset, limit):
        target = str(row["target"]).strip().lower()
        if target not in target_map:
            raise ValueError(f"Unexpected {config} target: {row['target']!r}")
        examples.append(
            Example(
                dataset=dataset_name,
                source=source,
                item_id=str(row_idx),
                question=relabel_dash_options(str(row["input"]).strip(), option_pairs),
                labels=[label for label, _ in option_pairs],
                gold=target_map[target],
                metadata={"target_text": row["target"], "config": config},
            )
        )
    return examples


def load_reclor_window(offset: int, limit: int) -> list[Example]:
    examples: list[Example] = []
    for row_idx, row in fetch_hf_rows_window("hadithya369/ReClor", "default", "validation", offset, limit):
        answers = [str(answer).strip() for answer in row["answers"]]
        labels = [chr(ord("A") + idx) for idx in range(len(answers))]
        options = "\n".join(f"({label}) {answer}" for label, answer in zip(labels, answers, strict=True))
        question = (
            f"Passage:\n{str(row['context']).strip()}\n\n"
            f"Question:\n{str(row['question']).strip()}\n\n"
            f"Options:\n{options}"
        )
        examples.append(
            Example(
                dataset="reclor",
                source="reclor_validation",
                item_id=str(row.get("id_string", row_idx)),
                question=question,
                labels=labels,
                gold=labels[int(row["label"])],
                metadata={
                    "context": row["context"],
                    "question": row["question"],
                    "answers": answers,
                },
            )
        )
    return examples


def letter_labels(count: int) -> list[str]:
    return [chr(ord("A") + idx) for idx in range(count)]


def choices_to_options(labels: list[str], texts: list[str]) -> str:
    return "\n".join(f"({label}) {text}" for label, text in zip(labels, texts, strict=True))


def load_logiqa_window(offset: int, limit: int) -> list[Example]:
    examples: list[Example] = []
    for row_idx, row in fetch_hf_rows_window("lucasmccabe/logiqa", "default", "validation", offset, limit):
        answers = [str(option).strip() for option in row["options"]]
        labels = letter_labels(len(answers))
        question = (
            f"Passage:\n{str(row['context']).strip()}\n\n"
            f"Question:\n{str(row['query']).strip()}\n\n"
            f"Options:\n{choices_to_options(labels, answers)}"
        )
        examples.append(
            Example(
                dataset="logiqa",
                source="logiqa_validation",
                item_id=str(row_idx),
                question=question,
                labels=labels,
                gold=labels[int(row["correct_option"])],
                metadata={"context": row["context"], "question": row["query"], "answers": answers},
            )
        )
    return examples


def load_choice_answerkey_window(
    *,
    dataset_id: str,
    config: str,
    split: str,
    dataset_name: str,
    source: str,
    question_field: str,
    offset: int,
    limit: int,
) -> list[Example]:
    examples: list[Example] = []
    for row_idx, row in fetch_hf_rows_window(dataset_id, config, split, offset, limit):
        choice_texts = [str(text).strip() for text in row["choices"]["text"]]
        source_labels = [str(label).strip() for label in row["choices"]["label"]]
        labels = letter_labels(len(choice_texts))
        answer_key = str(row["answerKey"]).strip()
        if answer_key in source_labels:
            gold = labels[source_labels.index(answer_key)]
        elif answer_key in labels:
            gold = answer_key
        else:
            raise ValueError(f"Could not map answerKey {answer_key!r} for {dataset_name}:{row_idx}")
        question = f"Question:\n{str(row[question_field]).strip()}\n\nOptions:\n{choices_to_options(labels, choice_texts)}"
        examples.append(
            Example(
                dataset=dataset_name,
                source=source,
                item_id=str(row.get("id", row_idx)),
                question=question,
                labels=labels,
                gold=gold,
                metadata={"question": row[question_field], "answers": choice_texts},
            )
        )
    return examples


def load_hellaswag_window(offset: int, limit: int) -> list[Example]:
    examples: list[Example] = []
    for row_idx, row in fetch_hf_rows_window("Rowan/hellaswag", "default", "validation", offset, limit):
        endings = [str(ending).strip() for ending in row["endings"]]
        labels = letter_labels(len(endings))
        question = (
            f"Context:\n{str(row['ctx']).strip()}\n\n"
            f"Activity: {str(row.get('activity_label', '')).strip()}\n\n"
            f"Which ending best continues the context?\n\n"
            f"Options:\n{choices_to_options(labels, endings)}"
        )
        examples.append(
            Example(
                dataset="hellaswag",
                source="hellaswag_validation",
                item_id=str(row_idx),
                question=question,
                labels=labels,
                gold=labels[int(row["label"])],
                metadata={"context": row["ctx"], "activity": row.get("activity_label", ""), "answers": endings},
            )
        )
    return examples


def load_winogrande_window(offset: int, limit: int) -> list[Example]:
    examples: list[Example] = []
    for row_idx, row in fetch_hf_rows_window(
        "allenai/winogrande",
        "winogrande_debiased",
        "validation",
        offset,
        limit,
    ):
        answers = [str(row["option1"]).strip(), str(row["option2"]).strip()]
        labels = ["A", "B"]
        answer = str(row["answer"]).strip()
        if answer not in {"1", "2"}:
            raise ValueError(f"Unexpected WinoGrande answer: {answer!r}")
        question = (
            f"Sentence:\n{str(row['sentence']).strip()}\n\n"
            "Which option should replace the blank?\n\n"
            f"Options:\n{choices_to_options(labels, answers)}"
        )
        examples.append(
            Example(
                dataset="winogrande",
                source="winogrande_debiased_validation",
                item_id=str(row_idx),
                question=question,
                labels=labels,
                gold=labels[int(answer) - 1],
                metadata={"sentence": row["sentence"], "answers": answers},
            )
        )
    return examples


def load_proofwriter_window(offset: int, limit: int) -> list[Example]:
    examples: list[Example] = []
    labels = ["A", "B", "C"]
    answer_map = {"true": "A", "false": "B", "unknown": "C"}
    for row_idx, row in fetch_hf_rows_window("tasksource/proofwriter", "default", "validation", offset, limit):
        answer = str(row["answer"]).strip().lower()
        if answer not in answer_map:
            raise ValueError(f"Unexpected ProofWriter answer: {row['answer']!r}")
        question = (
            f"Theory:\n{str(row['theory']).strip()}\n\n"
            f"Statement:\n{str(row['question']).strip()}\n\n"
            "Options:\n(A) True\n(B) False\n(C) Unknown"
        )
        examples.append(
            Example(
                dataset="proofwriter",
                source="proofwriter_validation",
                item_id=f"{row_idx}:{row.get('id', row_idx)}",
                question=question,
                labels=labels,
                gold=answer_map[answer],
                metadata={"theory": row["theory"], "question": row["question"], "answer_text": row["answer"]},
            )
        )
    return examples


def load_lsat_window(offset: int, limit: int) -> list[Example]:
    # This dataset is small enough that the existing loader is still acceptable,
    # but keep selection here so call sites share the same shape.
    return load_lsat_ar()[offset : offset + limit]


def load_pronto_window(offset: int, limit: int) -> list[Example]:
    return load_prontoqa()[offset : offset + limit]


def load_requested_dataset(name: str, offset: int, limit: int) -> list[Example]:
    if name == "bbh_logical_five":
        return load_bbh_mc(
            "logical_deduction_five_objects",
            "bbh_logical_five",
            "bbh_logical_deduction_five_objects",
            offset,
            limit,
        )
    if name == "bbh_logical_seven":
        return load_bbh_mc(
            "logical_deduction_seven_objects",
            "bbh_logical_seven",
            "bbh_logical_deduction_seven_objects",
            offset,
            limit,
        )
    if name == "bbh_tracking_five":
        return load_bbh_mc(
            "tracking_shuffled_objects_five_objects",
            "bbh_tracking_five",
            "bbh_tracking_shuffled_objects_five_objects",
            offset,
            limit,
        )
    if name == "bbh_tracking_seven":
        return load_bbh_mc(
            "tracking_shuffled_objects_seven_objects",
            "bbh_tracking_seven",
            "bbh_tracking_shuffled_objects_seven_objects",
            offset,
            limit,
        )
    if name == "bbh_web_lies":
        return load_bbh_web_of_lies(offset, limit)
    if name == "bbh_date":
        return load_bbh_mc("date_understanding", "bbh_date", "bbh_date_understanding", offset, limit)
    if name == "bbh_temporal":
        return load_bbh_mc("temporal_sequences", "bbh_temporal", "bbh_temporal_sequences", offset, limit)
    if name == "bbh_disambiguation":
        return load_bbh_mc("disambiguation_qa", "bbh_disambiguation", "bbh_disambiguation_qa", offset, limit)
    if name == "bbh_colored_objects":
        return load_bbh_mc(
            "reasoning_about_colored_objects",
            "bbh_colored_objects",
            "bbh_reasoning_about_colored_objects",
            offset,
            limit,
        )
    if name == "bbh_penguins":
        return load_bbh_mc("penguins_in_a_table", "bbh_penguins", "bbh_penguins_in_a_table", offset, limit)
    if name == "bbh_navigate":
        return load_bbh_binary(
            "navigate",
            "bbh_navigate",
            "bbh_navigate",
            offset,
            limit,
            [("A", "Yes"), ("B", "No")],
        )
    if name == "bbh_formal_fallacies":
        return load_bbh_binary(
            "formal_fallacies",
            "bbh_formal_fallacies",
            "bbh_formal_fallacies",
            offset,
            limit,
            [("A", "valid"), ("B", "invalid")],
        )
    if name == "reclor":
        return load_reclor_window(offset, limit)
    if name == "logiqa":
        return load_logiqa_window(offset, limit)
    if name == "qasc":
        return load_choice_answerkey_window(
            dataset_id="allenai/qasc",
            config="default",
            split="validation",
            dataset_name="qasc",
            source="qasc_validation",
            question_field="question",
            offset=offset,
            limit=limit,
        )
    if name == "openbookqa":
        return load_choice_answerkey_window(
            dataset_id="allenai/openbookqa",
            config="main",
            split="validation",
            dataset_name="openbookqa",
            source="openbookqa_main_validation",
            question_field="question_stem",
            offset=offset,
            limit=limit,
        )
    if name == "arc_challenge":
        return load_choice_answerkey_window(
            dataset_id="allenai/ai2_arc",
            config="ARC-Challenge",
            split="validation",
            dataset_name="arc_challenge",
            source="arc_challenge_validation",
            question_field="question",
            offset=offset,
            limit=limit,
        )
    if name == "hellaswag":
        return load_hellaswag_window(offset, limit)
    if name == "winogrande":
        return load_winogrande_window(offset, limit)
    if name == "proofwriter":
        return load_proofwriter_window(offset, limit)
    if name == "prontoqa":
        return load_pronto_window(offset, limit)
    if name == "lsat_ar":
        return load_lsat_window(offset, limit)
    raise ValueError(f"Unknown dataset: {name}")


def split_problem_and_options(question: str) -> tuple[str, str]:
    if "Options:" in question:
        problem, options = question.split("Options:", 1)
        return problem.strip(), options.strip()
    return question.strip(), ""


def option_label_map(options: str) -> str:
    pairs: list[str] = []
    for line in [line.strip() for line in options.splitlines() if line.strip()]:
        match = re.match(r"^\(?([A-Z])\)?\s*(.+)$", line)
        if not match:
            continue
        label, text = match.groups()
        text = text.strip().rstrip(".")
        text = re.sub(r"^(?:The\s+)?(.+?)\s+(?:is|are|has|finished|gets|holds|is dancing with|is playing)\b.*$", r"\1", text)
        pairs.append(f"{label}={text}")
    return ", ".join(pairs)


def common_option_target(options: str) -> str:
    cleaned = [
        re.sub(r"^\(?[A-Z]\)?\s*", "", line.strip()).strip()
        for line in options.splitlines()
        if line.strip()
    ]
    if not cleaned:
        return ""
    tokenized = [line.split() for line in cleaned]
    suffix: list[str] = []
    for columns in zip(*[list(reversed(tokens)) for tokens in tokenized]):
        if len({token.lower() for token in columns}) != 1:
            break
        suffix.append(columns[0])
    if len(suffix) >= 2:
        return " ".join(reversed(suffix))
    return cleaned[0]


def extract_bbh_entities(problem: str) -> str:
    patterns = [
        r"there (?:were|are) (?:three|five|seven) [^:]+:\s*([^.]+)\.",
        r"sells (?:three|five|seven) [^:]+:\s*([^.]+)\.",
        r"(?:three|five|seven) [^:]+:\s*([^.]+)\.",
    ]
    for pattern in patterns:
        match = re.search(pattern, problem, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split())
    return ""


def logical_deduction_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = [
        sentence
        for sentence in split_sentences(problem)
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
        "leftmost",
        "rightmost",
        "oldest",
        "newest",
        "cheapest",
        "expensive",
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
        "left of",
        "right of",
        "less expensive",
        "more expensive",
    )
    fixed = [sentence for sentence in sentences if any(word in sentence.lower() for word in fixed_words)]
    comparisons = [
        sentence
        for sentence in sentences
        if any(word in sentence.lower() for word in relation_words) and sentence not in fixed
    ]
    fixed_text = "\n".join(f"- {trim(sentence, 180)}" for sentence in fixed[:10]) or "- None explicit."
    comparison_text = "\n".join(f"- {trim(sentence, 180)}" for sentence in comparisons[:12]) or "- None explicit."
    return (
        "Transfer-structured order template:\n"
        "- Use one numbered order for the whole paragraph; decide which end is slot 1 from the wording.\n"
        "- Place exact/ordinal facts first, then apply comparison facts to the remaining open slots.\n"
        f"- Ordered items: {extract_bbh_entities(problem) or 'the listed objects'}\n"
        f"- Option labels: {option_label_map(options) or 'A-G as shown'}\n"
        f"- Shared option target: {common_option_target(options) or 'the requested rank/object'}\n"
        "- Exact/ordinal facts:\n"
        f"{fixed_text}\n"
        "- Comparison facts:\n"
        f"{comparison_text}\n"
        "- Answer by mapping the item in the target slot back to its label."
    )


def tracking_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    initial = [sentence for sentence in sentences if re.search(r"\b(at the start|initially|at the beginning)\b", sentence, re.I)]
    swaps = [
        sentence
        for sentence in sentences
        if re.search(r"^(First|Then|Finally),", sentence)
        and re.search(r"\b(swap|swaps|switch|switches|trade|trades)\b", sentence, re.I)
    ]
    query = ""
    query_match = re.search(r"(At the end[^\\n]+)$", problem, flags=re.IGNORECASE | re.DOTALL)
    if query_match:
        query = " ".join(query_match.group(1).split())
    return (
        "Transfer-structured state-tracking template:\n"
        "- Make a table with one row per person and one current held item/partner/position per row.\n"
        "- Initialize the table from the starting assignment sentence.\n"
        "- Apply swap events strictly in text order; a swap exchanges the current values of the two named people.\n"
        "- Do not compute from option order; map the final queried value back to its label only after all swaps.\n"
        f"- Option labels: {option_label_map(options) or 'A-G as shown'}\n"
        f"- Query: {trim(query, 240) or 'the final holder/item asked in the last sentence'}\n"
        "- Initial assignment sentence(s):\n"
        f"{chr(10).join(f'- {trim(sentence, 220)}' for sentence in initial[:3]) or '- Use the first assignment sentence in the prompt.'}\n"
        "- Swap sequence:\n"
        f"{chr(10).join(f'- {trim(sentence, 220)}' for sentence in swaps[:12]) or '- No swap sentence parsed; use the prompt order.'}"
    )


def web_lies_hint(example: Example) -> str:
    problem, _ = split_problem_and_options(example.question)
    problem = problem.removeprefix("Question:").strip()
    sentences = split_sentences(problem)
    query = ""
    statements: list[str] = []
    for sentence in sentences:
        if sentence.lower().startswith("does "):
            query = sentence
        else:
            statements.append(sentence)
    base = statements[:1]
    claims = statements[1:]
    return (
        "Transfer-structured truth-chain template:\n"
        "- Evaluate statements in sentence order, keeping a truth value for each named person.\n"
        "- A sentence 'X says Y tells the truth' is true exactly when Y tells the truth.\n"
        "- A sentence 'X says Y lies' is true exactly when Y lies.\n"
        "- Convert the final yes/no query to A=Yes or B=No after evaluating the chain.\n"
        f"- Query: {query or 'the final Does ... tell the truth? question'}\n"
        "- Base statement(s):\n"
        f"{chr(10).join(f'- {trim(sentence, 180)}' for sentence in base) or '- Use the first direct truth/lie sentence.'}\n"
        "- Chain statements:\n"
        f"{chr(10).join(f'- {trim(sentence, 180)}' for sentence in claims[:12]) or '- Use the remaining speaker statements in order.'}\n"
        "- Option labels: A=Yes, B=No"
    )


def date_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    date_mentions = unique_in_order(
        re.findall(
            r"\b(?:(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December)\.?\s+\d{1,2},\s+\d{4}|"
            r"\d{1,2}/\d{1,2}/\d{2,4}|(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)|"
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
            r"|(?:Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
            r"|Christmas Eve|Christmas|New Year's Eve|New Year's Day)\b",
            problem,
            flags=re.IGNORECASE,
        )
    )
    offset_sentence = ""
    for sentence in sentences:
        if re.search(r"\b(tomorrow|yesterday|ago|later|after|before|next|last)\b", sentence, re.I):
            offset_sentence = sentence
            break
    format_sentence = ""
    for sentence in sentences:
        if "MM/DD/YYYY" in sentence or "format" in sentence:
            format_sentence = sentence
            break
    return (
        "Transfer-structured date template:\n"
        "- Identify the anchor date exactly, including any locale-specific day/month wording.\n"
        "- Identify the requested offset such as tomorrow, yesterday, a week ago, a month later, or a year before.\n"
        "- Apply calendar arithmetic before comparing options; preserve the requested MM/DD/YYYY output format.\n"
        f"- Date/time mentions: {', '.join(date_mentions) or 'use the date mentions in the question'}\n"
        f"- Offset sentence: {trim(offset_sentence, 240) or 'the question sentence gives the requested offset'}\n"
        f"- Format sentence: {trim(format_sentence, 240) or 'answer in the option format shown'}\n"
        f"- Option labels: {option_label_map(options) or 'A-F as shown'}"
    )


def temporal_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    lines = [line.strip() for line in problem.splitlines() if line.strip()]
    target_line = lines[0] if lines else ""
    facts = [
        line
        for line in lines
        if re.search(r"\bfrom\b.+\bto\b|\bclosed after\b|\bwoke up\b", line, flags=re.IGNORECASE)
    ]
    return (
        "Transfer-structured temporal-interval template:\n"
        "- Build a day timeline from wake-up time through closing time.\n"
        "- Mark each witnessed activity interval as occupied.\n"
        "- The target visit must fit in an unoccupied interval and respect closing-time constraints.\n"
        "- Compare each option interval against the free intervals; do not choose an interval that overlaps a witnessed activity.\n"
        f"- Target event: {trim(target_line, 220) or 'the event asked in the first sentence'}\n"
        "- Timeline facts:\n"
        f"{chr(10).join(f'- {trim(fact, 180)}' for fact in facts[:14]) or '- Use the time facts in the prompt.'}\n"
        f"- Option labels: {option_label_map(options) or 'A-D as shown'}"
    )


def disambiguation_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentence_match = re.search(r"Sentence:\s*(.+)", problem, flags=re.IGNORECASE | re.DOTALL)
    sentence = " ".join(sentence_match.group(1).split()) if sentence_match else problem
    candidates = []
    for line in options.splitlines():
        cleaned = re.sub(r"^\([A-Z]\)\s*", "", line.strip())
        if cleaned and cleaned.lower() != "ambiguous":
            candidates.append(cleaned)
    return (
        "Transfer-structured pronoun-disambiguation template:\n"
        "- Identify the ambiguous pronoun and the candidate antecedents named in the sentence.\n"
        "- Test whether each candidate can grammatically and semantically satisfy the clause containing the pronoun.\n"
        "- Use the ambiguity option only if more than one candidate remains plausible from the sentence alone.\n"
        f"- Sentence to inspect: {trim(sentence, 300)}\n"
        f"- Candidate readings from options: {', '.join(candidates) or 'the non-ambiguous answer choices'}\n"
        f"- Option labels: {option_label_map(options) or 'A-C as shown'}"
    )


def colored_objects_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    inventory = ""
    query = problem
    inventory_match = re.search(r"\bthere (?:is|are)\s+(.+?)\.\s*(.+)$", problem, flags=re.IGNORECASE | re.DOTALL)
    if inventory_match:
        inventory = inventory_match.group(1)
        query = inventory_match.group(2)
    elif ". If " in problem:
        inventory, query_tail = problem.split(". If ", 1)
        query = "If " + query_tail
    quantity_phrases = re.findall(
        r"\b(?:a|an|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+[^,]+?(?=,\s|,\s+and\s|\s+and\s|$)",
        inventory,
        flags=re.IGNORECASE,
    )
    return (
        "Transfer-structured object-inventory template:\n"
        "- Parse the floor inventory into rows with quantity, color/modifier, and object type.\n"
        "- Apply any removal or filter operation before counting.\n"
        "- Count only objects matching the requested remaining color/type; ignore removed categories.\n"
        f"- Inventory phrases: {', '.join(quantity_phrases[:18]) or trim(inventory, 500)}\n"
        f"- Query/filter sentence: {trim(query, 300)}\n"
        "- Option labels: use the color/count options exactly as shown in the question."
    )


def penguins_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    question_match = re.search(r"(Which|What|How|Who).+$", problem, flags=re.IGNORECASE | re.DOTALL)
    focus = " ".join(question_match.group(0).split()) if question_match else "the final table question"
    added_rows = re.findall(r"We now add a penguin to the table:\s*([^\n]+)", problem, flags=re.IGNORECASE)
    table_match = re.search(r"first line is a header and each subsequent line is a penguin:\s*(.+?)For example:", problem, flags=re.IGNORECASE | re.DOTALL)
    table_text = " ".join(table_match.group(1).split()) if table_match else ""
    return (
        "Transfer-structured table-query template:\n"
        "- Use only the penguin table and any added penguin row; ignore distractor tables about other animals.\n"
        "- Keep columns as name, age, height, and weight.\n"
        "- Identify whether the final question asks for a row name, a column value, or a count over rows.\n"
        "- Apply table edits such as added or deleted rows before comparing with the option labels.\n"
        f"- Penguin table text: {trim(table_text, 650) or 'use the penguin table in the prompt'}\n"
        f"- Added penguin row(s): {', '.join(added_rows) or 'none'}\n"
        f"- Question focus: {trim(focus, 260)}\n"
        f"- Option labels: {option_label_map(options) or 'A-E as shown'}"
    )


def navigate_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    steps = re.findall(
        r"Take\s+\d+\s+steps?\s+(?:forward|backward|left|right)",
        problem,
        flags=re.IGNORECASE,
    )
    return (
        "Transfer-structured navigation template:\n"
        "- Track displacement on a 2D grid starting at (0, 0); do not rotate because the prompt says always face forward.\n"
        "- Treat forward/backward as one axis and left/right as the other axis.\n"
        "- Add each movement vector in order, then answer Yes only if the final displacement is back at (0, 0).\n"
        f"- Movement steps: {', '.join(steps) or 'use the movement instructions in order'}\n"
        f"- Option labels: {option_label_map(options) or 'A=Yes, B=No'}"
    )


def formal_fallacies_hint(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    argument_match = re.search(r'"(.+?)"', problem, flags=re.DOTALL)
    argument = " ".join(argument_match.group(1).split()) if argument_match else problem
    premise_markers = re.split(r"\b(?:In consequence|Therefore|Thus|Hence|So)\b", argument, maxsplit=1)
    premise_text = premise_markers[0].strip()
    conclusion_text = premise_markers[1].strip() if len(premise_markers) > 1 else "the final claim of the argument"
    return (
        "Transfer-structured formal-validity template:\n"
        "- Separate stated premises from the conclusion; judge only deductive validity, not real-world plausibility.\n"
        "- Check whether the conclusion must follow in every case where the premises are true.\n"
        "- Watch for converse or inverse errors such as turning 'all A are B' into 'all B are A'.\n"
        f"- Premise text: {trim(premise_text, 500)}\n"
        f"- Candidate conclusion text: {trim(conclusion_text, 300)}\n"
        f"- Option labels: {option_label_map(options) or 'A=valid, B=invalid'}"
    )


def reclor_hint(example: Example) -> str:
    context = str(example.metadata.get("context", ""))
    question = str(example.metadata.get("question", ""))
    answers = list(example.metadata.get("answers", []))
    conclusion = ""
    for marker in ("therefore", "thus", "hence", "so ", "conclude"):
        match = re.search(rf"\b{marker}\b(.+)$", context, flags=re.IGNORECASE)
        if match:
            conclusion = trim(match.group(0), 280)
            break
    labels = ", ".join(f"{chr(ord('A') + idx)}={trim(str(answer), 120)}" for idx, answer in enumerate(answers))
    return (
        "Transfer-structured logical-reading template:\n"
        "- Identify the passage's premises, conclusion, and any hidden assumption or flaw before reading choices.\n"
        "- Classify the question task: flaw, must-be-true, strengthen/weaken, parallel reasoning, or assumption.\n"
        "- Compare choices by role in the argument, not by surface word overlap.\n"
        f"- Question task: {trim(question, 260)}\n"
        f"- Possible conclusion cue: {conclusion or 'use the final main claim in the passage'}\n"
        f"- Answer-choice map: {labels or 'A-D as shown'}"
    )


def logiqa_hint(example: Example) -> str:
    context = str(example.metadata.get("context", ""))
    question = str(example.metadata.get("question", ""))
    answers = list(example.metadata.get("answers", []))
    labels = ", ".join(f"{chr(ord('A') + idx)}={trim(str(answer), 120)}" for idx, answer in enumerate(answers))
    return (
        "Transfer-structured logical-reading template:\n"
        "- Separate the passage's evidence, conclusion, and missing assumption before reading answer choices.\n"
        "- Classify the question task, such as evaluation, flaw, must-be-true, strengthen, weaken, or assumption.\n"
        "- Compare each option by its logical role in the argument rather than surface word overlap.\n"
        f"- Passage focus: {trim(context, 520)}\n"
        f"- Question task: {trim(question, 260)}\n"
        f"- Answer-choice map: {labels or 'A-D as shown'}"
    )


def science_question_hint(example: Example) -> str:
    question = str(example.metadata.get("question", ""))
    answers = list(example.metadata.get("answers", []))
    labels = ", ".join(f"{chr(ord('A') + idx)}={trim(str(answer), 90)}" for idx, answer in enumerate(answers))
    is_qasc = example.dataset == "qasc"
    return (
        "Transfer-structured science-choice template:\n"
        "- Identify the subject of the question and the property, process, cause, effect, or example being asked for.\n"
        "- Compare answer choices against that asked relation; eliminate choices with the wrong category or relation.\n"
        "- Use only the question and choices shown here; do not rely on hidden supporting facts.\n"
        f"- Question focus: {trim(question, 320)}\n"
        f"- Choice map: {labels or 'the answer choices shown'}\n"
        f"- Dataset condition: {'question-only QASC; hidden supporting facts are intentionally not provided.' if is_qasc else 'question-only science multiple choice.'}"
    )


def hellaswag_hint(example: Example) -> str:
    context = str(example.metadata.get("context", ""))
    activity = str(example.metadata.get("activity", ""))
    answers = list(example.metadata.get("answers", []))
    labels = ", ".join(f"{chr(ord('A') + idx)}={trim(str(answer), 100)}" for idx, answer in enumerate(answers))
    return (
        "Transfer-structured event-continuation template:\n"
        "- Preserve the same people, objects, location, and activity from the context.\n"
        "- Prefer the ending that is a plausible next physical action and keeps tense and agency consistent.\n"
        "- Reject endings that introduce unrelated objects, impossible actions, or a sudden scene change.\n"
        f"- Activity label: {activity or 'use the activity implied by the context'}\n"
        f"- Context: {trim(context, 420)}\n"
        f"- Ending map: {labels or 'A-D as shown'}"
    )


def winogrande_hint(example: Example) -> str:
    sentence = str(example.metadata.get("sentence", ""))
    answers = list(example.metadata.get("answers", []))
    labels = ", ".join(f"{chr(ord('A') + idx)}={trim(str(answer), 120)}" for idx, answer in enumerate(answers))
    return (
        "Transfer-structured blank-resolution template:\n"
        "- Read the full sentence and identify the semantic role required by the blank.\n"
        "- Test each candidate in the blank for agreement with nearby actions, distances, ownership, or cause/effect clues.\n"
        "- Choose the candidate that makes the sentence coherent, not merely the nearest noun.\n"
        f"- Sentence with blank: {trim(sentence, 420)}\n"
        f"- Candidate map: {labels or 'A/B as shown'}"
    )


def proofwriter_hint(example: Example) -> str:
    theory = str(example.metadata.get("theory", ""))
    query = str(example.metadata.get("question", ""))
    sentences = split_sentences(theory)
    rules = [
        sentence
        for sentence in sentences
        if re.search(r"\b(if|all|every|whoever|someone|people are|then)\b", sentence, flags=re.IGNORECASE)
    ]
    facts = [sentence for sentence in sentences if sentence not in rules]
    return (
        "Transfer-structured rule-entailment template:\n"
        "- Start from explicit facts, then repeatedly apply only forward rules whose conditions are already known.\n"
        "- Keep positive and negated properties distinct.\n"
        "- Answer True if the statement is derived, False if its negation is derived, and Unknown if neither is forced.\n"
        f"- Query statement: {trim(query, 220)}\n"
        "- Explicit facts:\n"
        f"{chr(10).join(f'- {trim(fact, 160)}' for fact in facts[:12]) or '- Use the fact sentences in the theory.'}\n"
        "- Rule sentences:\n"
        f"{chr(10).join(f'- {trim(rule, 180)}' for rule in rules[:14]) or '- No rule sentences parsed.'}\n"
        "- Option labels: A=True, B=False, C=Unknown"
    )


def pronto_hint(example: Example) -> str:
    context = str(example.metadata.get("context", ""))
    question = str(example.metadata.get("question", ""))
    sentences = split_sentences(context)
    query_statement = question
    match = re.search(r"\?\s*(.+?)\.?\s*$", question)
    if match:
        query_statement = match.group(1).strip().rstrip(".")

    subject = ""
    subject_match = re.match(r"Is the following statement true or false\?\s*([A-Z][A-Za-z]*)\b", question)
    if subject_match:
        subject = subject_match.group(1)
    else:
        simple = re.search(r"\b([A-Z][a-z]+)\s+(?:is|are)\b", query_statement)
        if simple:
            subject = simple.group(1)

    start_facts = [sentence for sentence in sentences if subject and subject.lower() in sentence.lower()]
    rules = [sentence for sentence in sentences if sentence not in start_facts]
    return (
        "Transfer-structured forward-chain template:\n"
        "- Start from explicit facts about the queried individual.\n"
        "- Repeatedly apply only forward rules whose premise class/property is already known.\n"
        "- Keep positive and negated properties separate; do not use rules backward.\n"
        f"- Query statement: {query_statement}\n"
        f"- Queried individual: {subject or 'the named subject'}\n"
        "- Starting fact(s):\n"
        f"{chr(10).join(f'- {trim(sentence, 180)}' for sentence in start_facts[:6]) or '- Use the explicit fact naming the queried individual.'}\n"
        "- Rule inventory, in prompt order:\n"
        f"{chr(10).join(f'- {trim(sentence, 180)}' for sentence in rules[:18])}"
    )


def lsat_hint(example: Example) -> str:
    question = example.question
    pre_q, post_q = (question.split("Q:", 1) + [""])[:2] if "Q:" in question else (question, "")
    setup = pre_q
    conditions = ""
    focus = ""
    for marker in (
        "according to the following conditions:",
        "The following conditions must apply:",
        "the following conditions must apply:",
        "The following conditions apply:",
        "the following conditions apply:",
    ):
        if marker in pre_q:
            setup, conditions = pre_q.split(marker, 1)
            break
    focus_match = re.search(r"^\s*(.*?)(?:Answer Choices:|Options:|$)", post_q, re.DOTALL)
    if focus_match:
        focus = trim(focus_match.group(1), 500)
    rules = split_sentences(conditions)
    return (
        "Transfer-structured LSAT-AR template:\n"
        "- Build a compact diagram from the setup before checking choices.\n"
        "- Separate capacity/slot rules, negative rules, and conditional rules.\n"
        "- For could-be-true or complete-schedule choices, check each answer against every rule literally.\n"
        f"- Setup: {trim(setup, 650)}\n"
        f"- Question focus: {focus or 'the question after Q:'}\n"
        "- Constraint sentences:\n"
        f"{chr(10).join(f'- {trim(rule, 220)}' for rule in rules[:14]) or '- Use all conditions stated before Q:.'}"
    )


def structured_hint(example: Example) -> str:
    if example.dataset in {"bbh_logical_five", "bbh_logical_seven"}:
        return logical_deduction_hint(example)
    if example.dataset in {"bbh_tracking_five", "bbh_tracking_seven"}:
        return tracking_hint(example)
    if example.dataset == "bbh_web_lies":
        return web_lies_hint(example)
    if example.dataset == "bbh_date":
        return date_hint(example)
    if example.dataset == "bbh_temporal":
        return temporal_hint(example)
    if example.dataset == "bbh_disambiguation":
        return disambiguation_hint(example)
    if example.dataset == "bbh_colored_objects":
        return colored_objects_hint(example)
    if example.dataset == "bbh_penguins":
        return penguins_hint(example)
    if example.dataset == "bbh_navigate":
        return navigate_hint(example)
    if example.dataset == "bbh_formal_fallacies":
        return formal_fallacies_hint(example)
    if example.dataset == "reclor":
        return reclor_hint(example)
    if example.dataset == "logiqa":
        return logiqa_hint(example)
    if example.dataset in {"qasc", "openbookqa", "arc_challenge"}:
        return science_question_hint(example)
    if example.dataset == "hellaswag":
        return hellaswag_hint(example)
    if example.dataset == "winogrande":
        return winogrande_hint(example)
    if example.dataset == "proofwriter":
        return proofwriter_hint(example)
    if example.dataset == "prontoqa":
        return pronto_hint(example)
    if example.dataset == "lsat_ar":
        return lsat_hint(example)
    raise ValueError(f"Unknown dataset for hint: {example.dataset}")


def build_hint(example: Example, level: str) -> str:
    if level == "none":
        return ""
    if level != "structured":
        raise ValueError(f"Unknown level: {level}")
    hint = structured_hint(example)
    # The generic guardrail bans the token "gold" to catch gold-label leaks, but
    # several datasets legitimately mention the color/material gold.
    validate_hint(re.sub(r"\bgold\b", "golden", hint, flags=re.IGNORECASE), example.gold)
    return hint


def build_prompt(example: Example, level: str) -> tuple[str, str]:
    hint = build_hint(example, level)
    task = "You are solving a multiple-choice reasoning question."
    if example.dataset in {"prontoqa", "bbh_web_lies", "proofwriter"}:
        task = "You are solving a true/false or yes/no reasoning question with lettered choices."
    prompt = f"{task}\n\n{example.question.strip()}\n"
    if hint:
        prompt += f"\nHint:\n{hint}\n"
    prompt += (
        "\nYour entire response must be exactly one of these labels: "
        f"{', '.join(example.labels)}. Do not write words or reasoning."
    )
    return prompt, hint


def run_generation(model: Any, tokenizer: Any, sampler: Any, user_prompt: str, max_tokens: int) -> str:
    from mlx_lm import generate

    messages = [
        {"role": "system", "content": "Output exactly one capital letter for the selected choice. Nothing else."},
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


def select_examples(examples: list[Example], offset: int, limit: int) -> list[Example]:
    # Loaders now already return the requested window. Keep this function for
    # compatibility with older call sites and dry-run snippets.
    return examples


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def make_record(
    *,
    run_id: str,
    example: Example,
    level: str,
    hint: str,
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


def pct(num: int, den: int) -> str:
    if den == 0:
        return "n/a"
    return f"{100.0 * num / den:.1f}%"


def stats_for(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_level: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_item: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        by_level[record["hint_level"]].append(record)
        by_item[record["id"]][record["hint_level"]] = record

    none = by_level["none"]
    structured = by_level["structured"]
    none_correct = [record for record in none if record["correct"]]
    none_wrong = [record for record in none if not record["correct"]]
    recovered = [
        record["id"]
        for record in none_wrong
        if by_item[record["id"]].get("structured", {}).get("correct", False)
    ]
    harmed = [
        record["id"]
        for record in none_correct
        if not by_item[record["id"]].get("structured", {}).get("correct", False)
    ]
    return {
        "none_correct": len(none_correct),
        "none_total": len(none),
        "structured_correct": sum(record["correct"] for record in structured),
        "structured_total": len(structured),
        "recovered": recovered,
        "none_wrong_total": len(none_wrong),
        "harmed": harmed,
        "none_correct_total": len(none_correct),
        "by_item": by_item,
    }


def write_summary(path: Path, records: list[dict[str, Any]], args: argparse.Namespace, run_id: str) -> None:
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_dataset[record["dataset"]].append(record)

    lines: list[str] = []
    lines.append("# Structured Transfer Eval")
    lines.append("")
    lines.append(f"- Run id: `{run_id}`")
    lines.append(f"- Model: `{args.model}`")
    lines.append("- Thinking mode: `enable_thinking=False`")
    lines.append(f"- Levels: `{', '.join(LEVELS)}`")
    lines.append(f"- Eval offset: `{args.eval_offset}`")
    lines.append(f"- Limit per dataset: `{args.limit}`")
    lines.append("")
    lines.append("| Dataset | Source | None | Structured | Delta | None-wrong recovered | None-correct harmed |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for dataset in sorted(by_dataset):
        st = stats_for(by_dataset[dataset])
        delta = st["structured_correct"] - st["none_correct"]
        lines.append(
            f"| `{dataset}` | {DATASET_INFO[dataset]['source']} | "
            f"{st['none_correct']}/{st['none_total']} ({pct(st['none_correct'], st['none_total'])}) | "
            f"{st['structured_correct']}/{st['structured_total']} ({pct(st['structured_correct'], st['structured_total'])}) | "
            f"{delta:+d} | {len(st['recovered'])}/{st['none_wrong_total']} | "
            f"{len(st['harmed'])}/{st['none_correct_total']} |"
        )
    lines.append("")
    lines.append("## Dataset Notes")
    lines.append("")
    for dataset in sorted(by_dataset):
        info = DATASET_INFO[dataset]
        st = stats_for(by_dataset[dataset])
        lines.append(f"### `{dataset}`")
        lines.append("")
        lines.append(f"- Dataset URL: {info['url']}")
        lines.append(f"- Template seed: {info['template_seed']}")
        lines.append(f"- Recovered rows: {', '.join(st['recovered']) or '-'}")
        lines.append(f"- Harmed rows: {', '.join(st['harmed']) or '-'}")
        lines.append("")
        lines.append("| Row | Gold | None | Structured |")
        lines.append("|---:|---:|---:|---:|")
        for item_id in sorted(st["by_item"], key=lambda value: (0, int(value)) if str(value).isdigit() else (1, str(value))):
            row = st["by_item"][item_id]
            lines.append(
                f"| {item_id} | {row['none']['gold']} | "
                f"{row['none']['parsed']} | {row['structured']['parsed']} |"
            )
        lines.append("")
    lines.append("## Guardrail")
    lines.append("")
    lines.append(
        "Structured hints are generated from question text only. They list task structure, "
        "entities, clue sentences, option maps, and reusable procedures, but do not compute "
        "final target candidates or answer letters."
    )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    choices = sorted(DATASET_INFO)
    parser = argparse.ArgumentParser(description="Run transfer-only structured hints on multiple datasets.")
    parser.add_argument("--datasets", nargs="+", default=choices, choices=choices)
    parser.add_argument("--eval-offset", type=int, default=20)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--results-dir", default="results/structured_transfer")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    selected: dict[str, list[Example]] = {}
    for dataset in args.datasets:
        print(f"[data] loading {dataset}", flush=True)
        examples = load_requested_dataset(dataset, args.eval_offset, args.limit)
        selected[dataset] = select_examples(examples, args.eval_offset, args.limit)
        print(
            f"[data] {dataset}: selected={len(selected[dataset])}",
            flush=True,
        )

    if args.dry_run:
        for dataset, examples in selected.items():
            for example in examples[:1]:
                for level in LEVELS:
                    prompt, _ = build_prompt(example, level)
                    print(f"\n===== {dataset} row {example.item_id} / {level} =====\n{prompt}")
        return 0

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or f"structured_transfer_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
            for level in LEVELS:
                user_prompt, hint = build_prompt(example, level)
                started = time.perf_counter()
                raw_text = run_generation(model, tokenizer, sampler, user_prompt, args.max_tokens)
                elapsed_s = time.perf_counter() - started
                record = make_record(
                    run_id=run_id,
                    example=example,
                    level=level,
                    hint=hint,
                    user_prompt=user_prompt,
                    raw_text=raw_text,
                    elapsed_s=elapsed_s,
                )
                records.append(record)
                append_jsonl(raw_path, record)

    write_summary(summary_path, records, args, run_id)
    print(f"[done] wrote {raw_path}", flush=True)
    print(f"[done] wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
