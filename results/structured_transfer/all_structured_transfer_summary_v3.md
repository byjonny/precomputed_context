# All Structured Transfer Summary v3

- Model: `Qwen/Qwen3.5-4B` via `mlx_lm`
- Thinking mode: `enable_thinking=False`; temperature `0`; answer constrained to one letter
- Structured boundary: reusable template + question-text extraction only; no final candidate propagation or answer-letter computation
- New in v3: LogiQA, QASC question-only, OpenBookQA question-only, ARC-Challenge, HellaSwag, WinoGrande, and ProofWriter.

| Dataset/config | Hint shape | None | Structured | Delta | Recovered | Harmed |
|---|---|---:|---:|---:|---:|---:|
| `ARC-Challenge validation` | question-only science-choice template | 12/12 (100.0%) | 12/12 (100.0%) | +0 | 0/0 | 0/12 |
| `BBH reasoning_about_colored_objects` | object inventory + filter/count template | 8/12 (66.7%) | 7/12 (58.3%) | -1 | 0/4 | 1/8 |
| `BBH date_understanding` | date anchor + offset + output-format template | 5/12 (41.7%) | 7/12 (58.3%) | +2 | 2/7 | 0/5 |
| `BBH disambiguation_qa` | pronoun/candidate/ambiguity template | 5/12 (41.7%) | 4/12 (33.3%) | -1 | 0/7 | 1/5 |
| `BBH formal_fallacies` | premise/conclusion validity template | 6/12 (50.0%) | 7/12 (58.3%) | +1 | 1/6 | 0/6 |
| `BBH logical_deduction_five_objects` | ordering fact-group template | 7/12 (58.3%) | 6/12 (50.0%) | -1 | 0/5 | 1/7 |
| `BBH navigate` | 2D displacement template | 10/12 (83.3%) | 10/12 (83.3%) | +0 | 0/2 | 0/10 |
| `BBH penguins_in_a_table` | table-edit/query template | 5/12 (41.7%) | 4/12 (33.3%) | -1 | 0/7 | 1/5 |
| `BBH temporal_sequences` | timeline/free-interval template | 11/12 (91.7%) | 11/12 (91.7%) | +0 | 0/1 | 0/11 |
| `BBH tracking_shuffled_objects_five_objects` | state table + ordered swaps template | 4/12 (33.3%) | 2/12 (16.7%) | -2 | 1/8 | 3/4 |
| `BBH tracking_shuffled_objects_seven_objects` | state table + ordered swaps template, larger arity | 3/12 (25.0%) | 2/12 (16.7%) | -1 | 0/9 | 1/3 |
| `BBH web_of_lies` | truth-chain template | 8/12 (66.7%) | 8/12 (66.7%) | +0 | 2/4 | 2/8 |
| `HellaSwag validation` | event-continuation plausibility template | 9/12 (75.0%) | 9/12 (75.0%) | +0 | 0/3 | 0/9 |
| `LogiQA validation` | logical-reading argument-role template | 8/12 (66.7%) | 8/12 (66.7%) | +0 | 0/4 | 0/8 |
| `AGIEval LSAT-AR` | setup/rules/focus diagram template | 4/12 (33.3%) | 3/12 (25.0%) | -1 | 1/8 | 2/4 |
| `OpenBookQA main validation, question-only` | question-only science-choice template | 12/12 (100.0%) | 12/12 (100.0%) | +0 | 0/0 | 0/12 |
| `ProntoQA` | forward-chain subject/rule inventory template | 10/12 (83.3%) | 11/12 (91.7%) | +1 | 1/2 | 0/10 |
| `ProofWriter validation` | facts/rules/query forward-chain template | 7/12 (58.3%) | 8/12 (66.7%) | +1 | 1/5 | 0/7 |
| `QASC validation, question-only` | question-only science-choice template | 9/12 (75.0%) | 8/12 (66.7%) | -1 | 0/3 | 1/9 |
| `ReClor validation` | logical-reading argument-role template | 8/12 (66.7%) | 9/12 (75.0%) | +1 | 2/4 | 1/8 |
| `WinoGrande debiased validation` | blank/candidate semantic-role template | 10/12 (83.3%) | 11/12 (91.7%) | +1 | 1/2 | 0/10 |
| **Total** |  | **161/252 (63.9%)** | **159/252 (63.1%)** | **-2** |  |  |

## Readout

- Across all tested configs so far, structured transfer is still slightly negative overall: 161/252 -> 159/252.
- New external batch alone is slightly positive: 67/84 -> 68/84, with gains on ProofWriter and WinoGrande.
- Saturated baselines limit interpretability for ARC-Challenge and OpenBookQA in this 12-row slice: both are already 12/12 without hints.
- Positive candidates to expand next: date understanding, ProofWriter, WinoGrande, ProntoQA, ReClor, and formal fallacies.
- Fragile/negative candidates remain state tracking, LSAT-AR, QASC question-only, pronoun disambiguation, colored-object inventory, and table editing.

## Dataset Sources

- BBH: https://huggingface.co/datasets/lukaemon/bbh
- LSAT-AR: https://huggingface.co/datasets/hails/agieval-lsat-ar
- ProntoQA: https://huggingface.co/datasets/renma/ProntoQA
- ReClor: https://huggingface.co/datasets/hadithya369/ReClor
- LogiQA: https://huggingface.co/datasets/lucasmccabe/logiqa
- QASC: https://huggingface.co/datasets/allenai/qasc
- OpenBookQA: https://huggingface.co/datasets/allenai/openbookqa
- ARC: https://huggingface.co/datasets/allenai/ai2_arc
- HellaSwag: https://huggingface.co/datasets/Rowan/hellaswag
- WinoGrande: https://huggingface.co/datasets/allenai/winogrande
- ProofWriter: https://huggingface.co/datasets/tasksource/proofwriter
