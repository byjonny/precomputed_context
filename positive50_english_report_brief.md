# Brief Report: Structured Hint Transferability, 50-Example Expansion

## Setup

- Model: `Qwen/Qwen3.5-4B` via `mlx_lm`
- Thinking mode: `enable_thinking=False`
- Decoding: temperature `0`; answer constrained to a single option letter
- Conditions compared: `none` vs `structured`
- Scope: seven datasets/configs that showed positive signal in earlier small-sample transfer runs

## 50-Example Results

| Dataset/config | Window | None | Structured | Delta | Recovered | Harmed |
|---|---|---:|---:|---:|---:|---:|
| BBH date_understanding | offset 20, rows 20-69 | 32/50 (64.0%) | 38/50 (76.0%) | +6 | 7/18 | 1/32 |
| ProntoQA | offset 20, ProntoQA_21-70 | 35/50 (70.0%) | 39/50 (78.0%) | +4 | 4/15 | 0/35 |
| BBH formal_fallacies | offset 20, rows 20-69 | 28/50 (56.0%) | 31/50 (62.0%) | +3 | 7/22 | 4/28 |
| ProofWriter | offset 20, rows 20-69 | 29/50 (58.0%) | 31/50 (62.0%) | +2 | 5/21 | 3/29 |
| WinoGrande | offset 20, rows 20-69 | 37/50 (74.0%) | 38/50 (76.0%) | +1 | 3/13 | 2/37 |
| BBH logical_deduction_seven_objects | offset 150, rows 150-199 | 30/50 (60.0%) | 31/50 (62.0%) | +1 | 4/20 | 3/30 |
| ReClor | offset 20, val_20-69 | 37/50 (74.0%) | 36/50 (72.0%) | -1 | 3/13 | 4/37 |
| **Total** | 350 examples | **228/350 (65.1%)** | **244/350 (69.7%)** | **+16** |  |  |

## Takeaways

- Overall, structured hints improved accuracy from `228/350` to `244/350` (`+16`).
- The strongest gains were on BBH date_understanding (`+6`), ProntoQA (`+4`), and BBH formal_fallacies (`+3`).
- ProofWriter, WinoGrande, and BBH logical_deduction_seven_objects were slightly positive.
- ReClor became slightly negative at 50 examples, so the earlier small-sample gain did not transfer reliably.
- Guardrail check: structured hints used only prompt-visible text and avoided direct answer phrases such as `answer is`, `correct option`, and `final answer`.

## Prompt Examples

For brevity, each dataset shows one representative prompt pair, usually a recovered case. The structured condition reused the same base prompt and added the shown hint block.

### BBH date_understanding

- Recovered example IDs: `21, 25, 33`
- Harmed example IDs: `66`
- Shown case: `21` (Recovered); gold `B`, none parsed `A`, structured parsed `B`

**None prompt excerpt**

```text
You are solving a multiple-choice reasoning question.

Yesterday, Jan 21, 2011, Jane ate 2 pizzas and 5 wings. What is the date 10 days ago in MM/DD/YYYY?
Options:
(A) 01/18/2011
(B) 01/12/2011
(C) 01/12/2069
(D) 01/13/2011
(E) 05/12/2010
(F) 08/12/2010

Your entire response must be exactly one of these labels: A, B, C, D, E, F. Do not write words or reasoning.
```

**Structured version: added hint block**

```text
Transfer-structured date template:
- Identify the anchor date exactly, including any locale-specific day/month wording.
- Identify the requested offset such as tomorrow, yesterday, a week ago, a month later, or a year before.
- Apply calendar arithmetic before comparing options; preserve the requested MM/DD/YYYY output format.
- Date/time mentions: Jan 21, 2011
- Offset sentence: Yesterday, Jan 21, 2011, Jane ate 2 pizzas and 5 wings.
- Format sentence: What is the date 10 days ago in MM/DD/YYYY?
- Option labels: A=01/18/2011, B=01/12/2011, C=01/12/2069, D=01/13/2011, E=05/12/2010, F=08/12/2010
```

### ProntoQA

- Recovered example IDs: `ProntoQA_28, ProntoQA_40, ProntoQA_45`
- Shown case: `ProntoQA_28` (Recovered); gold `B`, none parsed `A`, structured parsed `B`

**None prompt excerpt**

```text
You are solving a true/false or yes/no reasoning question with lettered choices.

Context:
Each impus is small. Each zumpus is not fruity. Every zumpus is a numpus. Each numpus is bitter. Numpuses are rompuses. Rompuses are kind. Rompuses are wumpuses. Every wumpus is not wooden. Wumpuses are yumpuses. Every yumpus is not temperate. Yumpuses are dumpuses. Every dumpus is dull. Dumpuses are tumpuses. Tumpuses are not small. Tumpuses are jompuses. Every jompus is nervous. Each jompus is a vumpus. Alex is a rompus.

Question:
Is the following statement true or false? Alex is small.

Options:
A) True
B) False

Your entire response must be exactly one of these labels: A, B. Do not write words or reasoning.
```

**Structured version: added hint block**

```text
Transfer-structured forward-chain template:
- Start from explicit facts about the queried individual.
- Repeatedly apply only forward rules whose premise class/property is already known.
- Keep positive and negated properties separate; do not use rules backward.
- Query statement: Alex is small
- Queried individual: Alex
- Starting fact(s):
- Alex is a rompus.
- Rule inventory, in prompt order:
- Each impus is small.
- Each zumpus is not fruity.
- Every zumpus is a numpus.
- Each numpus is bitter.
- Numpuses are rompuses.
- Rompuses are kind.
- Rompuses are wumpuses.
- Every wumpus is not wooden.
- Wumpuses are yumpuses.
- Every yumpus is not temperate.
- Yumpuses are dumpuses.
- Every dumpus is dull.
- Dumpuses are tumpuses.
- Tumpuses are not small.
- Tumpuses are jompuses.
- Every jompus is nervous.
- Each jompus is a vumpus.
```

### BBH formal_fallacies

- Recovered example IDs: `20, 36, 49`
- Harmed example IDs: `38, 43, 45`
- Shown case: `20` (Recovered); gold `B`, none parsed `A`, structured parsed `B`

**None prompt excerpt**

```text
You are solving a multiple-choice reasoning question.

"Is Fred a fan of Liverpool? Are supporters of Real Madrid devotees of PSG? In European football, it is sometimes difficult to keep track of the mutual admiration and dislike. The following argument seeks to clarify some such relations: Every supporter of Tottenham Hotspur is not an expert of Trabzonspor AŞ and not a backer of US Sassuolo Calcio. Every backer of US Sassuolo Calcio who is an expert of Trabzonspor AŞ is a supporter of Tottenham Hotspur or a devotee of FC Zenit. In consequence, everyone who is not both an expert of Trabzonspor AŞ and a backer of US Sassuolo Calcio is a devotee of FC Zenit."
Is the argume
...[truncated for brevity]
```

**Structured version: added hint block**

```text
Transfer-structured formal-validity template:
- Separate stated premises from the conclusion; judge only deductive validity, not real-world plausibility.
- Check whether the conclusion must follow in every case where the premises are true.
- Watch for converse or inverse errors such as turning 'all A are B' into 'all B are A'.
- Premise text: Is Fred a fan of Liverpool? Are supporters of Real Madrid devotees of PSG? In European football, it is sometimes difficult to keep track of the mutual admiration and dislike. The following argument seeks to clarify some such relations: Every supporter of Tottenham Hotspur is not an expert of Trabzonspor AŞ and not a backer of US Sassuolo Calcio. Every backer of US Sassuolo Calcio who is an expert of Trabzonspor AŞ is a supporter of Tottenham Hotspur or a devotee of FC Ze
...[truncated for brevity]
```

### ProofWriter

- Recovered example IDs: `23:RelNoneg-OWA-D0-5791, 41:AttNeg-OWA-D0-1627, 46:AttNeg-OWA-D0-4365`
- Harmed example IDs: `35:AttNoneg-OWA-D0-6891, 57:RelNeg-OWA-D0-1507, 61:RelNeg-OWA-D0-4996`
- Shown case: `23:RelNoneg-OWA-D0-5791` (Recovered); gold `C`, none parsed `B`, structured parsed `C`

**None prompt excerpt**

```text
You are solving a true/false or yes/no reasoning question with lettered choices.

Theory:
The tiger is blue. The tiger is green. The tiger is kind. The tiger is rough. The tiger is young. Green, kind people are blue. If someone is young and green then they are rough. All young people are green. Blue, young people are rough. Young, blue people are green. Blue, green people are rough.

Statement:
The tiger sees the tiger.

Options:
(A) True
(B) False
(C) Unknown

Your entire response must be exactly one of these labels: A, B, C. Do not write words or reasoning.
```

**Structured version: added hint block**

```text
Transfer-structured rule-entailment template:
- Start from explicit facts, then repeatedly apply only forward rules whose conditions are already known.
- Keep positive and negated properties distinct.
- Answer True if the statement is derived, False if its negation is derived, and Unknown if neither is forced.
- Query statement: The tiger sees the tiger.
- Explicit facts:
- The tiger is blue.
- The tiger is green.
- The tiger is kind.
- The tiger is rough.
- The tiger is young.
- Rule sentences:
- Green, kind people are blue.
- If someone is young and green then they are rough.
- All young people are green.
- Blue, young people are rough.
- Young, blue people are green.
- Blue, green people are rough.
- Option labels: A=True, B=False, C=Unknown
```

### WinoGrande

- Recovered example IDs: `26, 60, 62`
- Harmed example IDs: `45, 54`
- Shown case: `26` (Recovered); gold `A`, none parsed `B`, structured parsed `A`

**None prompt excerpt**

```text
You are solving a multiple-choice reasoning question.

Sentence:
All the clutter in the house excited Leslie but not Derrick because cleaning energized _ very much.

Which option should replace the blank?

Options:
(A) Leslie
(B) Derrick

Your entire response must be exactly one of these labels: A, B. Do not write words or reasoning.
```

**Structured version: added hint block**

```text
Transfer-structured blank-resolution template:
- Read the full sentence and identify the semantic role required by the blank.
- Test each candidate in the blank for agreement with nearby actions, distances, ownership, or cause/effect clues.
- Choose the candidate that makes the sentence coherent, not merely the nearest noun.
- Sentence with blank: All the clutter in the house excited Leslie but not Derrick because cleaning energized _ very much.
- Candidate map: A=Leslie, B=Derrick
```

### BBH logical_deduction_seven_objects

- Recovered example IDs: `167, 173, 177`
- Harmed example IDs: `164, 179, 181`
- Shown case: `167` (Recovered); gold `G`, none parsed `A`, structured parsed `G`

**None prompt excerpt**

```text
You are solving a multiple-choice reasoning question.

The following paragraphs each describe a set of seven objects arranged in a fixed order. The statements are logically consistent within each paragraph. In a golf tournament, there were seven golfers: Ada, Ana, Rob, Amy, Dan, Joe, and Eli. Eli finished below Amy. Ada finished third. Amy finished below Rob. Dan finished last. Rob finished second. Ana finished fourth.
Options:
(A) Ada finished second-to-last
(B) Ana finished second-to-last
(C) Rob finished second-to-last
(D) Amy finished second-to-last
(E) Dan finished second-to-last
(F) Joe finished second-to-last
(G) Eli finished second-to-last

Your entire response mu
...[truncated for brevity]
```

**Structured version: added hint block**

```text
Transfer-structured order template:
- Use one numbered order for the whole paragraph; decide which end is slot 1 from the wording.
- Place exact/ordinal facts first, then apply comparison facts to the remaining open slots.
- Ordered items: Ada, Ana, Rob, Amy, Dan, Joe, and Eli
- Option labels: A=Ada, B=Ana, C=Rob, D=Amy, E=Dan, F=Joe, G=Eli
- Shared option target: finished second-to-last
- Exact/ordinal facts:
- Ada finished third.
- Dan finished last.
- Rob finished second.
- Ana finished fourth.
- Comparison facts:
- Eli finished below Amy.
- Amy finished below Rob.
- Answer by mapping the item in the target slot back to its label.
```

### ReClor

- Recovered example IDs: `val_28, val_30, val_57`
- Harmed example IDs: `val_25, val_39, val_47`
- Shown case: `val_28` (Recovered); gold `C`, none parsed `D`, structured parsed `C`

**None prompt excerpt**

```text
You are solving a multiple-choice reasoning question.

Passage:
The short-term and long-term interests of a business often conflict; when they do, the morally preferable act is usually the one that serves the long-term interest. Because of this, businesses often have compelling reasons to execute the morally preferable act.

Question:
Which one of the following, if assumed, enables the conclusion of the argument to be properly drawn?

Options:
(A) When a business's short-term and long-term interests conflict, morality alone is rarely the overriding consideration.
(B) The morally preferable act for a business to execute and the long-term interests of the business seldom co
...[truncated for brevity]
```

**Structured version: added hint block**

```text
Transfer-structured logical-reading template:
- Identify the passage's premises, conclusion, and any hidden assumption or flaw before reading choices.
- Classify the question task: flaw, must-be-true, strengthen/weaken, parallel reasoning, or assumption.
- Compare choices by role in the argument, not by surface word overlap.
- Question task: Which one of the following, if assumed, enables the conclusion of the argument to be properly drawn?
- Possible conclusion cue: use the final main claim in the passage
- Answer-choice map: A=When a business's short-term and long-term interests conflict, morality alone is rarely the overriding consideration., B=The morally preferable act for a business to execute and the long-term interests of the business seldom conflict., C=A business's long-term interests often provide
...[truncated for brevity]
```

## Raw Artifacts

- `results/structured_transfer/positive50_structured_v1.jsonl`
- `results/structured_transfer/positive50_bbh_logical_seven_v1.jsonl`
- `results/structured_transfer/positive50_combined_summary.md`
- `results/structured_transfer/positive50_english_report.md` contains fuller prompt examples.
