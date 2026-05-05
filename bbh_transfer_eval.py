#!/usr/bin/env python3
"""Transfer learned BBH hint shapes to held-out logical-deduction examples.

The prompts here are derived from the earlier BBH hint-lab cases, then applied
unchanged to later BBH examples. The structured condition uses only automatic
problem parsing, not gold labels or hand-written per-example reasoning.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from run_context_eval import MODEL_ID, Example, load_bbh_config, parse_answer


LEVELS = ["none", "structured", "generalized", "minimal"]


GENERALIZED_V1 = (
    "Use one numbered rank scale for the whole problem. First decide which end is rank 1 "
    "from the wording, including first/last, top/bottom, oldest/newest, cheapest/most expensive, "
    "or above/below. Translate relative targets such as third-to-last or third-newest onto that "
    "same scale. Place exact-rank facts first, then fit comparison chains into the remaining "
    "open slots before matching the target rank to an option."
)

MINIMAL_V1 = (
    "Use one numbered order. Place exact positions first, apply comparison chains to the open "
    "positions, then check the requested target rank."
)

GENERALIZED_V2 = (
    "Internally make a seven-slot table before answering. Normalize every clue to the same order "
    "direction, put fixed ordinal clues into the table, and use each comparison only to constrain "
    "the still-empty slots. Do not answer from the first plausible option; answer only after the "
    "target slot or target object is forced."
)

MINIMAL_V2 = (
    "Make a seven-slot rank table, fill fixed clues, resolve comparisons, then map the forced "
    "slot to its option."
)


def split_problem_and_options(question: str) -> tuple[str, str]:
    if "Options:" in question:
        problem, options = question.split("Options:", 1)
        return problem.strip(), options.strip()
    return question.strip(), ""


def split_sentences(text: str) -> list[str]:
    return [piece.strip() for piece in re.split(r"(?<=[.!?])\s+", text.strip()) if piece.strip()]


def ordinal_phrase(sentence: str) -> bool:
    return bool(
        re.search(
            r"\b(first|second|third|fourth|fifth|sixth|seventh|last|"
            r"top|bottom|oldest|newest|cheapest|expensive|highest|lowest)\b",
            sentence,
            flags=re.IGNORECASE,
        )
    )


def fixed_position_phrase(sentence: str) -> bool:
    return bool(
        re.search(
            r"\b(first|second|third|fourth|fifth|sixth|seventh|last|"
            r"leftmost|rightmost|newest|oldest|cheapest|"
            r"\d+(?:st|nd|rd|th)(?:-| )?(?:oldest|newest|cheapest)|"
            r"(?:second|third|fourth|fifth|sixth)(?:-| )?(?:oldest|newest|cheapest)|"
            r"(?:second|third|fourth|fifth|sixth)(?:-| )?most expensive|"
            r"(?:second|third|fourth|fifth|sixth) from the (?:left|right))\b",
            sentence,
            flags=re.IGNORECASE,
        )
    )


def comparison_phrase(sentence: str) -> bool:
    return bool(
        re.search(
            r"\b(above|below|older than|newer than|cheaper than|"
            r"more expensive than|less expensive than|higher than|lower than|"
            r"larger than|smaller than|before|after|less than|more than|"
            r"to the left of|to the right of)\b",
            sentence,
            flags=re.IGNORECASE,
        )
    )


def extract_entities(problem: str) -> str:
    patterns = [
        r"there (?:were|are) seven [^:]+:\s*([^.]+)\.",
        r"sells seven [^:]+:\s*([^.]+)\.",
        r"seven [^:]+:\s*([^.]+)\.",
    ]
    for pattern in patterns:
        match = re.search(pattern, problem, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split())
    return ""


def option_target(options: str) -> str:
    lines = [line.strip() for line in options.splitlines() if line.strip()]
    cleaned: list[str] = []
    for line in lines:
        line = re.sub(r"^\([A-Z]\)\s*", "", line).strip()
        cleaned.append(line)
    if not cleaned:
        return ""

    # BBH logical-deduction options usually share everything except the object.
    # Keep a compact human-readable sample if common-suffix extraction is brittle.
    tokenized = [line.split() for line in cleaned]
    suffix: list[str] = []
    for columns in zip(*[list(reversed(tokens)) for tokens in tokenized]):
        lowered = {token.lower() for token in columns}
        if len(lowered) != 1:
            break
        suffix.append(columns[0])
    if len(suffix) >= 2:
        return " ".join(reversed(suffix))
    return cleaned[0]


def option_label_objects(options: str) -> str:
    lines = [line.strip() for line in options.splitlines() if line.strip()]
    pairs: list[str] = []
    for line in lines:
        match = re.match(r"^\(([A-Z])\)\s*(.+)$", line)
        if not match:
            continue
        label, text = match.groups()
        text = text.strip().rstrip(".")

        # The BBH logical-deduction choices differ mainly by the object name.
        object_match = re.match(
            r"^(?:The\s+)?(.+?)\s+(?:is|are|finished)\b",
            text,
            flags=re.IGNORECASE,
        )
        if object_match:
            item = object_match.group(1).strip()
        else:
            item = text
        pairs.append(f"{label}={item}")
    return ", ".join(pairs)


def structured_v1(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    fact_sentences = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
    ]
    exact = [sentence for sentence in fact_sentences if ordinal_phrase(sentence)]
    comparisons = [sentence for sentence in fact_sentences if comparison_phrase(sentence)]
    # Avoid duplicating exact ordinal facts under comparisons when possible.
    comparison_only = [sentence for sentence in comparisons if sentence not in exact]
    exact_text = "\n".join(f"- {sentence}" for sentence in exact[:10]) or "- No explicit fixed-rank facts found."
    comparison_text = "\n".join(f"- {sentence}" for sentence in comparison_only[:12]) or "- No explicit comparison facts found."
    entities = extract_entities(problem)
    target = option_target(options)

    return (
        "Precomputed structure from the problem text:\n"
        f"- Ordered items: {entities or 'the seven listed objects'}\n"
        f"- Shared option target: {target or 'identify the requested rank/object'}\n"
        "- Fixed or ordinal facts:\n"
        f"{exact_text}\n"
        "- Remaining comparison facts:\n"
        f"{comparison_text}\n"
        "Normalize these facts onto one rank scale before choosing."
    )


def structured_v2(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    facts = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
    ]
    fact_text = "\n".join(f"- {sentence}" for sentence in facts[:14])
    return (
        "Precomputed rank-table scaffold:\n"
        "- Create seven ordered slots: 1, 2, 3, 4, 5, 6, 7.\n"
        f"- Items: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"- Target phrase from options: {option_target(options) or 'the requested option property'}\n"
        "- Clues to translate into the table:\n"
        f"{fact_text}\n"
        "Use the scaffold to fill slots, not to guess from option order."
    )


def structured_v3(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    fact_sentences = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]
    fixed = [sentence for sentence in fact_sentences if fixed_position_phrase(sentence)]
    comparisons = [
        sentence
        for sentence in fact_sentences
        if comparison_phrase(sentence) and sentence not in fixed
    ]
    fixed_text = "\n".join(f"- {sentence}" for sentence in fixed[:10]) or "- No fixed slot facts."
    comparison_text = "\n".join(f"- {sentence}" for sentence in comparisons[:12]) or "- No pairwise order facts."

    return (
        "Precomputed ordered-constraint structure:\n"
        "- Use seven slots numbered 1 through 7 on one consistent scale.\n"
        f"- Items: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"- Target from options: {option_target(options) or 'the requested rank/object'}\n"
        "- Fixed slot facts to place first:\n"
        f"{fixed_text}\n"
        "- Pairwise order facts to apply after fixed slots:\n"
        f"{comparison_text}\n"
        "Convert clues like from the right, newest, oldest, cheapest, most expensive, left, "
        "right, above, and below onto the same slot scale before matching the option."
    )


ORDINALS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
}


def split_entities(entity_text: str) -> list[str]:
    if not entity_text:
        return []
    normalized = entity_text.replace(", and ", ", ").replace(" and ", ", ")
    entities = []
    for part in normalized.split(","):
        entity = re.sub(r"^(?:a|an|the)\s+", "", part.strip(), flags=re.IGNORECASE)
        if entity:
            entities.append(entity)
    return entities


def normalize_for_match(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_entities(sentence: str, entities: list[str]) -> list[str]:
    norm_sentence = normalize_for_match(sentence)
    found: list[tuple[int, str]] = []
    for entity in entities:
        norm_entity = normalize_for_match(entity)
        match = re.search(rf"\b{re.escape(norm_entity)}\b", norm_sentence)
        if match:
            found.append((match.start(), entity))
    return [entity for _, entity in sorted(found)]


def infer_scale(problem: str, options: str) -> tuple[str, str]:
    text = f"{problem}\n{options}".lower()
    if "finished" in text or "golf tournament" in text:
        return "finish rank", "slot 1 = first / highest finish"
    if "left" in text or "right" in text or "branch" in text or "shelf" in text:
        return "left-to-right position", "slot 1 = leftmost"
    if "older" in text or "newer" in text or "car show" in text:
        return "age rank", "slot 1 = oldest"
    if "expensive" in text or "cheapest" in text or "fruit stand" in text:
        return "price rank", "slot 1 = most expensive"
    return "rank", "slot 1 = the first/highest/leftmost end named by the problem"


def ordinal_word_number(text: str) -> int | None:
    for word, number in ORDINALS.items():
        if re.search(rf"\b{word}\b", text, flags=re.IGNORECASE):
            return number
    return None


def parse_slot(text: str, scale_name: str) -> int | None:
    lowered = text.lower()
    number = ordinal_word_number(lowered)

    if "leftmost" in lowered or "rightmost" in lowered:
        return 1 if "leftmost" in lowered else 7
    if "from the left" in lowered:
        return number
    if "from the right" in lowered:
        return 8 - number if number else None

    if scale_name == "finish rank":
        if "last" in lowered:
            if "second" in lowered:
                return 6
            if "third" in lowered:
                return 5
            return 7
        return number

    if scale_name == "age rank":
        if "oldest" in lowered:
            return number or 1
        if "newest" in lowered:
            return 8 - (number or 1)

    if scale_name == "price rank":
        if "cheapest" in lowered:
            return 8 - (number or 1)
        if "most expensive" in lowered:
            return number or 1

    return number


def normalized_constraints(example: Example) -> dict[str, Any]:
    problem, options = split_problem_and_options(example.question)
    entities = split_entities(extract_entities(problem))
    scale_name, scale_description = infer_scale(problem, options)
    target = option_target(options)
    target_slot = parse_slot(target, scale_name)
    facts = [
        sentence
        for sentence in split_sentences(problem)
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]

    fixed: list[str] = []
    fixed_pairs: list[tuple[str, int]] = []
    comparisons: list[str] = []
    comparison_pairs: list[tuple[str, str, str]] = []
    for sentence in facts:
        mentioned = find_entities(sentence, entities)
        if not mentioned:
            continue
        slot = parse_slot(sentence, scale_name)
        if slot is not None and fixed_position_phrase(sentence):
            fixed.append(f"{mentioned[0]} = slot {slot} ({sentence})")
            fixed_pairs.append((mentioned[0], slot))
            continue

        if len(mentioned) >= 2 and comparison_phrase(sentence):
            left, right = mentioned[0], mentioned[1]
            lowered = sentence.lower()
            if any(phrase in lowered for phrase in ["below", "newer than", "less expensive than", "to the right of"]):
                comparisons.append(f"{left} > {right} ({sentence})")
                comparison_pairs.append((left, ">", right))
            elif any(phrase in lowered for phrase in ["above", "older than", "more expensive than", "to the left of"]):
                comparisons.append(f"{left} < {right} ({sentence})")
                comparison_pairs.append((left, "<", right))
            else:
                comparisons.append(f"{left} ? {right} ({sentence})")

    return {
        "entities": entities,
        "scale_name": scale_name,
        "scale_description": scale_description,
        "target": target,
        "target_slot": target_slot,
        "fixed": fixed,
        "fixed_pairs": fixed_pairs,
        "comparisons": comparisons,
        "comparison_pairs": comparison_pairs,
    }


def structured_v4(example: Example) -> str:
    data = normalized_constraints(example)
    fixed_text = "\n".join(f"- {item}" for item in data["fixed"][:10]) or "- No fixed slot facts."
    comparison_text = "\n".join(f"- {item}" for item in data["comparisons"][:12]) or "- No pairwise order facts."
    target_slot = f"slot {data['target_slot']}" if data["target_slot"] is not None else "the target slot named by the options"
    return (
        "Precomputed normalized rank structure:\n"
        f"- Scale: {data['scale_name']} ({data['scale_description']}).\n"
        f"- Items: {', '.join(data['entities']) or 'the seven listed objects'}\n"
        f"- Option target: {data['target'] or 'the requested rank/object'} -> {target_slot}.\n"
        "- Fixed slot facts:\n"
        f"{fixed_text}\n"
        "- Pairwise order constraints, where '<' means earlier/left/older/more expensive/higher on this scale:\n"
        f"{comparison_text}\n"
        "Fill the remaining slots with these constraints, then choose the option naming the item in the target slot."
    )


def solve_constraints(data: dict[str, Any]) -> dict[str, Any]:
    entities = list(data["entities"])
    if len(entities) != 7:
        return {"solution_count": None, "target_items": []}
    fixed_pairs = list(data["fixed_pairs"])
    comparison_pairs = list(data["comparison_pairs"])
    target_slot = data["target_slot"]
    solutions: list[dict[str, int]] = []

    for slots in itertools.permutations(range(1, 8), len(entities)):
        assignment = dict(zip(entities, slots))
        if any(assignment.get(entity) != slot for entity, slot in fixed_pairs):
            continue
        ok = True
        for left, op, right in comparison_pairs:
            if op == "<" and not assignment[left] < assignment[right]:
                ok = False
                break
            if op == ">" and not assignment[left] > assignment[right]:
                ok = False
                break
        if ok:
            solutions.append(assignment)

    target_items: list[str] = []
    if target_slot is not None:
        target_items = sorted(
            {
                entity
                for solution in solutions
                for entity, slot in solution.items()
                if slot == target_slot
            }
        )
    return {
        "solution_count": len(solutions),
        "target_items": target_items,
    }


def structured_v5(example: Example) -> str:
    data = normalized_constraints(example)
    fixed_text = "\n".join(f"- {item}" for item in data["fixed"][:10]) or "- No fixed slot facts."
    comparison_text = "\n".join(f"- {item}" for item in data["comparisons"][:12]) or "- No pairwise order facts."
    solved = solve_constraints(data)
    target_slot = f"slot {data['target_slot']}" if data["target_slot"] is not None else "the target slot named by the options"
    if solved["solution_count"] is None:
        propagation = "- Constraint propagation skipped because the seven items could not be parsed cleanly."
    else:
        candidates = ", ".join(solved["target_items"]) or "no parsed candidate"
        propagation = (
            f"- Parsed legal arrangements: {solved['solution_count']}\n"
            f"- Possible item(s) in {target_slot}: {candidates}"
        )
    return (
        "Precomputed normalized structure plus target-slot propagation:\n"
        f"- Scale: {data['scale_name']} ({data['scale_description']}).\n"
        f"- Items: {', '.join(data['entities']) or 'the seven listed objects'}\n"
        f"- Option target: {data['target'] or 'the requested rank/object'} -> {target_slot}.\n"
        "- Fixed slot facts:\n"
        f"{fixed_text}\n"
        "- Pairwise order constraints, where '<' means earlier/left/older/more expensive/higher on this scale:\n"
        f"{comparison_text}\n"
        "- Constraint propagation summary:\n"
        f"{propagation}\n"
        "Choose the option whose item is in the propagated target slot. Do not use option order as a shortcut."
    )


def structured_v6(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    fact_sentences = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]
    fixed = [sentence for sentence in fact_sentences if fixed_position_phrase(sentence)]
    comparisons = [
        sentence
        for sentence in fact_sentences
        if comparison_phrase(sentence) and sentence not in fixed
    ]
    fixed_text = "\n".join(f"- {sentence}" for sentence in fixed[:10]) or "- No fixed-position clues."
    comparison_text = "\n".join(f"- {sentence}" for sentence in comparisons[:12]) or "- No comparison-chain clues."
    return (
        "Transfer-structured hint learned from prior BBH ordering examples:\n"
        "- First build one seven-slot order. Decide what slot 1 means from the wording.\n"
        f"- Items to place: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"- Target phrase to answer: {option_target(options) or 'the requested option property'}\n"
        "- Put these fixed-position clues into the slots first:\n"
        f"{fixed_text}\n"
        "- Then use these comparison-chain clues to fill the remaining slots:\n"
        f"{comparison_text}\n"
        "- After the slots are filled, return the option naming the item at the target position."
    )


def structured_v7(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    facts = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]
    facts_text = "\n".join(f"- {sentence}" for sentence in facts[:12])
    return (
        "Structured transfer context:\n"
        f"Items: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"Target: {option_target(options) or 'the requested rank/object'}\n"
        "Clues:\n"
        f"{facts_text}\n"
        "Use a seven-position table. Translate every clue into the same table, then inspect the target position."
    )


def structured_v8(example: Example) -> str:
    data = normalized_constraints(example)
    fixed_text = "\n".join(f"- {item}" for item in data["fixed"][:10]) or "- No fixed slot facts."
    comparison_text = "\n".join(f"- {item}" for item in data["comparisons"][:12]) or "- No pairwise order facts."
    target_slot = f"slot {data['target_slot']}" if data["target_slot"] is not None else "the target slot named by the options"
    return (
        "Normalized structured transfer hint:\n"
        f"- Scale: {data['scale_name']} ({data['scale_description']}).\n"
        f"- Target: {data['target'] or 'the requested rank/object'} -> {target_slot}.\n"
        "- Fixed slot constraints:\n"
        f"{fixed_text}\n"
        "- Pairwise constraints (`<` means earlier/left/older/more expensive/higher on this scale):\n"
        f"{comparison_text}\n"
        "Use these constraints to fill the slots yourself; no target item has been precomputed."
    )


def structured_v9(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    fact_sentences = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]
    fixed = [sentence for sentence in fact_sentences if fixed_position_phrase(sentence)]
    comparisons = [
        sentence
        for sentence in fact_sentences
        if comparison_phrase(sentence) and sentence not in fixed
    ]
    fixed_text = "\n".join(f"- {sentence}" for sentence in fixed[:10]) or "- No fixed-position clues."
    comparison_text = "\n".join(f"- {sentence}" for sentence in comparisons[:12]) or "- No comparison-chain clues."
    return (
        "Transfer-structured hint from prior BBH ordering failures:\n"
        "- Build the full seven-slot order internally before answering; do not default to the first or last option.\n"
        "- Convert targets such as leftmost, rightmost, newest, oldest, second-cheapest, and third-from-right to one slot direction.\n"
        "- Extreme targets often come from comparison chains or the only remaining item, not only from fixed-position clues.\n"
        f"- Items: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"- Target phrase: {option_target(options) or 'the requested rank/object'}\n"
        "- Fixed-position clues:\n"
        f"{fixed_text}\n"
        "- Comparison-chain clues:\n"
        f"{comparison_text}\n"
        "- Fill fixed slots, propagate every comparison transitively, then choose the option naming the item in the target slot."
    )


def structured_v10(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    fact_sentences = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]
    fixed = [sentence for sentence in fact_sentences if fixed_position_phrase(sentence)]
    comparisons = [
        sentence
        for sentence in fact_sentences
        if comparison_phrase(sentence) and sentence not in fixed
    ]
    fixed_text = "\n".join(f"- {sentence}" for sentence in fixed[:10]) or "- No fixed-position clues."
    comparison_text = "\n".join(f"- {sentence}" for sentence in comparisons[:12]) or "- No comparison-chain clues."
    return (
        "Transfer-structured option-check hint learned from earlier BBH order tasks:\n"
        "- Use the same seven-slot order for every clue; decide which end is slot 1 from the wording.\n"
        "- Do not answer from option order. For each label, test whether that item can occupy the target position.\n"
        "- Reject a label if putting its item at the target position violates a fixed-position clue or any comparison chain.\n"
        f"- Items: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"- Option label map: {option_label_objects(options) or 'use the option labels in the question'}\n"
        f"- Target phrase to test: {option_target(options) or 'the requested rank/object'}\n"
        "- Fixed-position clues:\n"
        f"{fixed_text}\n"
        "- Comparison-chain clues:\n"
        f"{comparison_text}\n"
        "- Choose the label whose item survives the full consistency check."
    )


def structured_v11(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    fact_sentences = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]
    fixed = [sentence for sentence in fact_sentences if fixed_position_phrase(sentence)]
    comparisons = [
        sentence
        for sentence in fact_sentences
        if comparison_phrase(sentence) and sentence not in fixed
    ]
    fixed_text = "\n".join(f"- {sentence}" for sentence in fixed[:10]) or "- No fixed-position clues."
    comparison_text = "\n".join(f"- {sentence}" for sentence in comparisons[:12]) or "- No comparison-chain clues."
    return (
        "Transfer-structured empty-slot hint from earlier BBH order tasks:\n"
        "- Draw slots 1-7 first. Put every exact ordinal clue into its slot before using comparisons.\n"
        "- Cross out occupied slots and placed items; the target may be forced by the remaining open slot/item.\n"
        "- For left/right/newest/oldest/cheapest/finish wording, keep one consistent direction for all seven slots.\n"
        "- Use comparison chains to bound which remaining items can be before/after each other; do not pick an endpoint by default.\n"
        f"- Items: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"- Option label map: {option_label_objects(options) or 'use the option labels in the question'}\n"
        f"- Target phrase: {option_target(options) or 'the requested rank/object'}\n"
        "- Exact/ordinal clues:\n"
        f"{fixed_text}\n"
        "- Order-chain clues:\n"
        f"{comparison_text}\n"
        "- Answer with the label for the item forced into the target slot after elimination."
    )


def structured_v12(example: Example) -> str:
    problem, options = split_problem_and_options(example.question)
    sentences = split_sentences(problem)
    facts = [
        sentence
        for sentence in sentences
        if not sentence.lower().startswith("the following paragraphs each describe")
        and not re.search(r"\b(?:there (?:were|are)|sells) seven\b", sentence, flags=re.IGNORECASE)
    ]
    facts_text = "\n".join(f"- {sentence}" for sentence in facts[:14])
    return (
        "Transfer-structured compact checklist:\n"
        f"- Items: {extract_entities(problem) or 'the seven listed objects'}\n"
        f"- Labels: {option_label_objects(options) or 'A-G as shown'}\n"
        f"- Asked position/property: {option_target(options) or 'the shared option target'}\n"
        "- Clues from the paragraph:\n"
        f"{facts_text}\n"
        "- Solve by filling a seven-slot table, then map the item in the asked position back to its label."
    )


def build_hint(example: Example, level: str, variant: str) -> str:
    if level == "none":
        return ""
    if variant == "v1":
        if level == "structured":
            return structured_v1(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v2":
        if level == "structured":
            return structured_v2(example)
        if level == "generalized":
            return GENERALIZED_V2
        if level == "minimal":
            return MINIMAL_V2
    if variant == "v3":
        if level == "structured":
            return structured_v3(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v4":
        if level == "structured":
            return structured_v4(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v5":
        if level == "structured":
            return structured_v5(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v6":
        if level == "structured":
            return structured_v6(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v7":
        if level == "structured":
            return structured_v7(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v8":
        if level == "structured":
            return structured_v8(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v9":
        if level == "structured":
            return structured_v9(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v10":
        if level == "structured":
            return structured_v10(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v11":
        if level == "structured":
            return structured_v11(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    if variant == "v12":
        if level == "structured":
            return structured_v12(example)
        if level == "generalized":
            return GENERALIZED_V1
        if level == "minimal":
            return MINIMAL_V1
    raise ValueError(f"Unknown variant/level: {variant}/{level}")


def build_prompt(example: Example, level: str, variant: str) -> tuple[str, str]:
    hint = build_hint(example, level, variant)
    prompt = f"You are solving a multiple-choice logical-deduction question.\n\n{example.question.strip()}\n"
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


def select_examples(args: argparse.Namespace) -> list[Example]:
    examples = load_bbh_config(
        "logical_deduction_seven_objects",
        "bbh_logical_deduction_seven_objects",
    )
    train_ids = {"34", "54", "99", "209", "212"}
    selected = [
        example
        for example in examples
        if int(example.item_id) >= args.start_id and example.item_id not in train_ids
    ]
    return selected[: args.limit]


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        handle.flush()


def summarize(records: list[dict[str, Any]], variant: str, levels: list[str]) -> str:
    by_level: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_item: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for record in records:
        by_level[record["hint_level"]].append(record)
        by_item[record["id"]][record["hint_level"]] = record

    lines: list[str] = []
    lines.append(f"# BBH Transfer Eval ({variant})")
    lines.append("")
    lines.append("- Dataset: `lukaemon/bbh`, config `logical_deduction_seven_objects`")
    lines.append("- Test split: held-out row ids after the BBH hint-lab examples")
    lines.append("- Model: `Qwen/Qwen3.5-4B`, `enable_thinking=False`, temperature 0")
    lines.append("")
    lines.append("| Level | Accuracy | Delta vs none | None-wrong recovered | None-correct preserved |")
    lines.append("|---|---:|---:|---:|---:|")

    base = by_level["none"]
    base_correct = sum(record["correct"] for record in base)
    base_total = len(base)
    base_acc = base_correct / base_total if base_total else 0.0
    none_wrong = [record for record in base if not record["correct"]]
    none_correct = [record for record in base if record["correct"]]

    for level in levels:
        rows = by_level[level]
        correct = sum(record["correct"] for record in rows)
        total = len(rows)
        acc = correct / total if total else 0.0
        delta = acc - base_acc
        if level == "none":
            recovered = "n/a"
            preserved = "n/a"
        else:
            recovered_n = sum(
                1
                for record in none_wrong
                if by_item[record["id"]].get(level, {}).get("correct", False)
            )
            preserved_n = sum(
                1
                for record in none_correct
                if by_item[record["id"]].get(level, {}).get("correct", False)
            )
            recovered = f"{recovered_n}/{len(none_wrong)}"
            preserved = f"{preserved_n}/{len(none_correct)}"
        lines.append(
            f"| `{level}` | {correct}/{total} ({acc:.1%}) | {delta:+.1%} | {recovered} | {preserved} |"
        )

    lines.append("")
    lines.append("## Per-Example Outputs")
    lines.append("")
    lines.append("| Row | Gold | None | Structured | Generalized | Minimal |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    for item_id in sorted(by_item, key=lambda x: int(x)):
        row = by_item[item_id]
        lines.append(
            "| "
            + " | ".join(
                [
                    item_id,
                    row["none"]["gold"],
                    str(row.get("none", {}).get("parsed")),
                    str(row.get("structured", {}).get("parsed")),
                    str(row.get("generalized", {}).get("parsed")),
                    str(row.get("minimal", {}).get("parsed")),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transfer BBH learned hint templates to held-out examples.")
    parser.add_argument(
        "--variant",
        choices=["v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9", "v10", "v11", "v12"],
        default="v1",
    )
    parser.add_argument(
        "--levels",
        nargs="+",
        default=LEVELS,
        choices=LEVELS,
        help="Hint levels to run. Include `none` for accuracy deltas.",
    )
    parser.add_argument("--start-id", type=int, default=213)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=16)
    parser.add_argument("--results-dir", default="results/bbh_transfer")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    examples = select_examples(args)
    if not examples:
        raise ValueError("No examples selected.")

    levels = list(dict.fromkeys(args.levels))
    if "none" not in levels:
        levels = ["none"] + levels

    if args.dry_run:
        for example in examples[:3]:
            for level in levels:
                prompt, _ = build_prompt(example, level, args.variant)
                print(f"\n===== row {example.item_id} / {level} =====\n{prompt}")
        return 0

    run_id = args.run_id or f"{args.variant}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
    for example in examples:
        for level in levels:
            user_prompt, hint = build_prompt(example, level, args.variant)
            print(f"[run] row={example.item_id} level={level}", flush=True)
            started = time.perf_counter()
            raw_text = run_generation(model, tokenizer, sampler, user_prompt, args.max_tokens)
            elapsed_s = time.perf_counter() - started
            parsed = parse_answer(raw_text, example.labels)
            record = {
                "run_id": run_id,
                "variant": args.variant,
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
            }
            records.append(record)
            append_jsonl(raw_path, record)

    summary_path.write_text(summarize(records, args.variant, levels), encoding="utf-8")
    print(f"[done] wrote {raw_path}", flush=True)
    print(f"[done] wrote {summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
