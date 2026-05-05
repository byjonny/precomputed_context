# Structured Transfer Eval

- Run id: `external_dataset_structured_v1`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Levels: `none, structured`
- Eval offset: `20`
- Limit per dataset: `12`

| Dataset | Source | None | Structured | Delta | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `arc_challenge` | allenai/ai2_arc:ARC-Challenge/validation | 12/12 (100.0%) | 12/12 (100.0%) | +0 | 0/0 | 0/12 |
| `hellaswag` | Rowan/hellaswag:validation | 9/12 (75.0%) | 9/12 (75.0%) | +0 | 0/3 | 0/9 |
| `logiqa` | lucasmccabe/logiqa:validation | 8/12 (66.7%) | 8/12 (66.7%) | +0 | 0/4 | 0/8 |
| `openbookqa` | allenai/openbookqa:main/validation | 12/12 (100.0%) | 12/12 (100.0%) | +0 | 0/0 | 0/12 |
| `proofwriter` | tasksource/proofwriter:validation | 7/12 (58.3%) | 8/12 (66.7%) | +1 | 1/5 | 0/7 |
| `qasc` | allenai/qasc:validation | 9/12 (75.0%) | 8/12 (66.7%) | -1 | 0/3 | 1/9 |
| `winogrande` | allenai/winogrande:winogrande_debiased/validation | 10/12 (83.3%) | 11/12 (91.7%) | +1 | 1/2 | 0/10 |

## Dataset Notes

### `arc_challenge`

- Dataset URL: https://huggingface.co/datasets/allenai/ai2_arc
- Template seed: First few ARC-Challenge examples: classify the science question type and compare choices to the asked property.
- Recovered rows: -
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| MCAS_2000_8_10 | B | B | B |
| MCAS_2005_8_5 | D | D | D |
| MCAS_2012_5_8 | B | B | B |
| MCAS_2015_8_7 | B | B | B |
| Mercury_184765 | B | B | B |
| Mercury_405454 | D | D | D |
| Mercury_7115063 | A | A | A |
| Mercury_7179358 | B | B | B |
| Mercury_7187915 | A | A | A |
| Mercury_7189823 | A | A | A |
| Mercury_7217053 | B | B | B |
| Mercury_SC_LBS10040 | D | D | D |

### `hellaswag`

- Dataset URL: https://huggingface.co/datasets/Rowan/hellaswag
- Template seed: First few HellaSwag examples: preserve event participants, action continuity, and physical plausibility.
- Recovered rows: -
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | A | A |
| 21 | A | A | A |
| 22 | D | D | D |
| 23 | D | D | D |
| 24 | A | A | A |
| 25 | D | A | A |
| 26 | A | A | A |
| 27 | D | D | D |
| 28 | B | C | C |
| 29 | D | D | D |
| 30 | B | B | B |
| 31 | A | A | A |

### `logiqa`

- Dataset URL: https://huggingface.co/datasets/lucasmccabe/logiqa
- Template seed: First few LogiQA examples: separate argument text, question task, and answer-choice roles.
- Recovered rows: -
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | C | C | C |
| 21 | D | A | C |
| 22 | A | B | B |
| 23 | D | A | A |
| 24 | D | D | D |
| 25 | B | B | B |
| 26 | B | B | B |
| 27 | C | C | C |
| 28 | D | D | D |
| 29 | B | A | A |
| 30 | D | D | D |
| 31 | D | D | D |

### `openbookqa`

- Dataset URL: https://huggingface.co/datasets/allenai/openbookqa
- Template seed: First few OpenBookQA examples: identify science relation in the question and eliminate implausible choices.
- Recovered rows: -
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 230 | A | A | A |
| 231 | B | B | B |
| 529 | D | D | D |
| 1565 | A | A | A |
| 1981 | A | A | A |
| 7-1139 | C | C | C |
| 7-131 | C | C | C |
| 7-289 | A | A | A |
| 7-606 | D | D | D |
| 7-847 | C | C | C |
| 8-162 | D | D | D |
| 9-472 | B | B | B |

### `proofwriter`

- Dataset URL: https://huggingface.co/datasets/tasksource/proofwriter
- Template seed: First few ProofWriter examples: forward-chain from facts and rules to the queried statement.
- Recovered rows: 23:RelNoneg-OWA-D0-5791
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20:RelNoneg-OWA-D0-5791 | A | A | A |
| 21:RelNoneg-OWA-D0-5791 | B | A | A |
| 22:RelNoneg-OWA-D0-5791 | C | C | C |
| 23:RelNoneg-OWA-D0-5791 | C | B | C |
| 24:AttNeg-OWA-D0-5908 | A | A | A |
| 25:AttNeg-OWA-D0-5908 | B | C | A |
| 26:AttNeg-OWA-D0-5908 | C | C | C |
| 27:AttNeg-OWA-D0-5908 | C | C | C |
| 28:AttNeg-OWA-D0-2030 | A | A | A |
| 29:AttNeg-OWA-D0-2030 | B | B | B |
| 30:AttNeg-OWA-D0-2030 | C | A | A |
| 31:AttNeg-OWA-D0-2030 | C | B | B |

### `qasc`

- Dataset URL: https://huggingface.co/datasets/allenai/qasc
- Template seed: First few QASC examples: identify asked concept/property and compare choices using question text only.
- Recovered rows: -
- Harmed rows: 37FMASSAYCQQJSQKMCPQKQYCAY6IBK

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 30IQTZXKAK5MP0C5NIS23JP879AX0E | A | A | A |
| 31LVTDXBL79FP0FF3C8TCLV89HRLRO | E | D | D |
| 32KTQ2V7RDETRI1E979MLDA33HLM9C | A | G | G |
| 37FMASSAYCQQJSQKMCPQKQYCAY6IBK | C | C | G |
| 3H7Z272LX76UDNZ0QK447QVT8X0LPP | A | A | A |
| 3IUZPWIU1O69DQEJH66YKKQACBBKWR | C | C | C |
| 3PW9OPU9PQJLV9UQVCB9RYEM1KT21B | E | C | C |
| 3QFUFYSY9YEMO23L6P9I9FFEK3OF4P | G | G | G |
| 3QY5DC2MXRJL50X0LV00MJD8LE2FU0 | C | C | C |
| 3TAYZSBPLL7LPTTK8VQTNZ1VPXK2SX | F | F | F |
| 3TE22NPXPBBCQM6WM8DZIBINWS3449 | C | C | C |
| 3V0Z7YWSIYZ1HLAO2QVYYML2OL9V2U | F | F | F |

### `winogrande`

- Dataset URL: https://huggingface.co/datasets/allenai/winogrande
- Template seed: First few WinoGrande examples: compare candidate fillers by semantic role in the sentence.
- Recovered rows: 26
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | B | B |
| 21 | B | B | B |
| 22 | B | A | A |
| 23 | A | A | A |
| 24 | B | B | B |
| 25 | A | A | A |
| 26 | A | B | A |
| 27 | A | A | A |
| 28 | A | A | A |
| 29 | A | A | A |
| 30 | A | A | A |
| 31 | A | A | A |

## Guardrail

Structured hints are generated from question text only. They list task structure, entities, clue sentences, option maps, and reusable procedures, but do not compute final target candidates or answer letters.
