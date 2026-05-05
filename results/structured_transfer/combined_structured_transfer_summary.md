# Multi-Dataset Structured Transfer Summary

- Model: `Qwen/Qwen3.5-4B` via `mlx_lm`
- Thinking mode: `enable_thinking=False`
- Sampling: `temperature=0`, one-letter answer only
- Evaluation window: offset `20`, limit `12` per dataset/config
- Structured context boundary: reusable template plus question-text extraction only; no final candidate propagation or answer-letter computation

| Dataset/config | Hint shape | None | Structured | Delta | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `BBH date_understanding` | structured date anchor + offset + format template | 5/12 (41.7%) | 7/12 (58.3%) | +2 | 2/7 | 0/5 |
| `BBH logical_deduction_five_objects` | transferred BBH ordering fact-group template | 7/12 (58.3%) | 6/12 (50.0%) | -1 | 0/5 | 1/7 |
| `BBH temporal_sequences` | timeline/free-interval template | 11/12 (91.7%) | 11/12 (91.7%) | +0 | 0/1 | 0/11 |
| `BBH tracking_shuffled_objects_five_objects` | state table + ordered swaps template | 4/12 (33.3%) | 2/12 (16.7%) | -2 | 1/8 | 3/4 |
| `BBH tracking_shuffled_objects_seven_objects` | same state table template at larger arity | 3/12 (25.0%) | 2/12 (16.7%) | -1 | 0/9 | 1/3 |
| `BBH web_of_lies` | truth-chain sentence-order template | 8/12 (66.7%) | 8/12 (66.7%) | +0 | 2/4 | 2/8 |
| `AGIEval LSAT-AR` | setup/rules/focus LSAT diagram template | 4/12 (33.3%) | 3/12 (25.0%) | -1 | 1/8 | 2/4 |
| `ProntoQA` | forward-chain subject/rule inventory template | 10/12 (83.3%) | 11/12 (91.7%) | +1 | 1/2 | 0/10 |
| **Total** | across 8 configs | **52/96 (54.2%)** | **50/96 (52.1%)** | **-2** |  |  |

## Readout

- Positive transfer showed up on `BBH date_understanding` (+2/12) and `ProntoQA` (+1/12), both without harming baseline-correct examples.
- `BBH temporal_sequences` was saturated already: 11/12 baseline and 11/12 with structured context.
- `BBH web_of_lies` had recoveries and harms that cancelled out, suggesting the fixed truth-chain wording biases the model toward `A=Yes` on this slice.
- `BBH tracking`, `BBH logical_five`, and `LSAT-AR` were negative with the first transferable templates; the structured text often changed the answer but did not reliably move it toward gold.
- Overall, this round does not support a broad claim that structured-level transfer hints improve non-thinking Qwen. It suggests transferability is task-shape dependent, with date arithmetic and forward-chain rule tasks as the best candidates to expand next.

## Raw Result Files

- `results/structured_transfer/multi_dataset_structured_v1.jsonl`
- `results/structured_transfer/multi_dataset_structured_v1_more_bbh.jsonl`
