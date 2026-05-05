# Structured Transfer Eval

- Run id: `multi_dataset_structured_v1`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Levels: `none, structured`
- Eval offset: `20`
- Limit per dataset: `12`

| Dataset | Source | None | Structured | Delta | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `bbh_logical_five` | lukaemon/bbh:logical_deduction_five_objects | 7/12 (58.3%) | 6/12 (50.0%) | -1 | 0/5 | 1/7 |
| `bbh_tracking_five` | lukaemon/bbh:tracking_shuffled_objects_five_objects | 4/12 (33.3%) | 2/12 (16.7%) | -2 | 1/8 | 3/4 |
| `bbh_tracking_seven` | lukaemon/bbh:tracking_shuffled_objects_seven_objects | 3/12 (25.0%) | 2/12 (16.7%) | -1 | 0/9 | 1/3 |
| `bbh_web_lies` | lukaemon/bbh:web_of_lies | 8/12 (66.7%) | 8/12 (66.7%) | +0 | 2/4 | 2/8 |
| `lsat_ar` | hails/agieval-lsat-ar:test | 4/12 (33.3%) | 3/12 (25.0%) | -1 | 1/8 | 2/4 |
| `prontoqa` | renma/ProntoQA:dev_gpt4 | 10/12 (83.3%) | 11/12 (91.7%) | +1 | 1/2 | 0/10 |

## Dataset Notes

### `bbh_logical_five`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: Earlier BBH logical-deduction examples used for v1/v6 transfer templates.
- Recovered rows: -
- Harmed rows: 25

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | B | B |
| 21 | C | A | D |
| 22 | B | A | E |
| 23 | A | B | B |
| 24 | D | D | D |
| 25 | B | B | E |
| 26 | E | E | E |
| 27 | E | A | D |
| 28 | A | A | A |
| 29 | D | B | B |
| 30 | B | B | B |
| 31 | C | C | C |

### `bbh_tracking_five`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: First few shuffled-object examples: initialize holder table, apply swaps in order.
- Recovered rows: 23
- Harmed rows: 20, 25, 26

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | E | E | D |
| 21 | A | E | E |
| 22 | E | E | E |
| 23 | E | A | E |
| 24 | C | E | E |
| 25 | B | B | E |
| 26 | A | A | E |
| 27 | E | A | A |
| 28 | D | A | A |
| 29 | A | C | E |
| 30 | D | E | E |
| 31 | D | E | E |

### `bbh_tracking_seven`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: Same shuffled-object table template transferred to seven-object cases.
- Recovered rows: -
- Harmed rows: 21

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | C | B | G |
| 21 | A | A | G |
| 22 | F | A | G |
| 23 | D | G | G |
| 24 | B | A | A |
| 25 | G | G | G |
| 26 | B | G | G |
| 27 | E | F | F |
| 28 | G | G | G |
| 29 | D | G | B |
| 30 | E | G | G |
| 31 | D | G | G |

### `bbh_web_lies`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: First few truth-chain examples: evaluate speaker claims in sentence order.
- Recovered rows: 20, 24
- Harmed rows: 27, 30

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | A | B | A |
| 21 | A | A | A |
| 22 | A | A | A |
| 23 | B | A | A |
| 24 | A | B | A |
| 25 | A | A | A |
| 26 | A | A | A |
| 27 | B | B | A |
| 28 | A | A | A |
| 29 | A | A | A |
| 30 | B | B | A |
| 31 | B | A | A |

### `lsat_ar`

- Dataset URL: https://huggingface.co/datasets/hails/agieval-lsat-ar
- Template seed: Earlier LSAT-AR examples: setup/rules/focus decomposition before checking choices.
- Recovered rows: 25
- Harmed rows: 29, 30

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | D | A | A |
| 21 | B | A | E |
| 22 | A | A | A |
| 23 | D | A | A |
| 24 | C | A | E |
| 25 | E | C | E |
| 26 | E | A | A |
| 27 | D | A | A |
| 28 | A | B | B |
| 29 | A | A | E |
| 30 | A | A | D |
| 31 | C | C | C |

### `prontoqa`

- Dataset URL: https://huggingface.co/datasets/renma/ProntoQA
- Template seed: Earlier ProntoQA hint-lab cases: forward-chain from subject facts to query predicate.
- Recovered rows: ProntoQA_28
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| ProntoQA_21 | A | A | A |
| ProntoQA_22 | B | A | A |
| ProntoQA_23 | A | A | A |
| ProntoQA_24 | A | A | A |
| ProntoQA_25 | A | A | A |
| ProntoQA_26 | A | A | A |
| ProntoQA_27 | A | A | A |
| ProntoQA_28 | B | A | B |
| ProntoQA_29 | B | B | B |
| ProntoQA_30 | A | A | A |
| ProntoQA_31 | A | A | A |
| ProntoQA_32 | A | A | A |

## Guardrail

Structured hints are generated from question text only. They list task structure, entities, clue sentences, option maps, and reusable procedures, but do not compute final target candidates or answer letters.
