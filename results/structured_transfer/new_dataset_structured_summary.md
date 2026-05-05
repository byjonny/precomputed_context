# New Dataset Structured Transfer Summary

- Model: `Qwen/Qwen3.5-4B` via `mlx_lm`
- Thinking mode: `enable_thinking=False`; temperature `0`; answer constrained to one letter
- Structured boundary: reusable template + question-text extraction only; no final candidate propagation or answer-letter computation
- Note: This file combines the five completed BBH configs from `new_dataset_structured_v1.jsonl` with the clean ReClor rerun.

| Dataset/config | Hint shape | None | Structured | Delta | Recovered | Harmed |
|---|---|---:|---:|---:|---:|---:|
| `BBH reasoning_about_colored_objects` | object inventory + filter/count template | 8/12 (66.7%) | 7/12 (58.3%) | -1 | 0/4 | 1/8 |
| `BBH disambiguation_qa` | pronoun/candidate/ambiguity template | 5/12 (41.7%) | 4/12 (33.3%) | -1 | 0/7 | 1/5 |
| `BBH formal_fallacies` | premise/conclusion validity template | 6/12 (50.0%) | 7/12 (58.3%) | +1 | 1/6 | 0/6 |
| `BBH navigate` | 2D displacement template | 10/12 (83.3%) | 10/12 (83.3%) | +0 | 0/2 | 0/10 |
| `BBH penguins_in_a_table` | table-edit/query template | 5/12 (41.7%) | 4/12 (33.3%) | -1 | 0/7 | 1/5 |
| `ReClor validation` | logical-reading argument-role template | 8/12 (66.7%) | 9/12 (75.0%) | +1 | 2/4 | 1/8 |
| **Total** |  | **42/72 (58.3%)** | **41/72 (56.9%)** | **-1** |  |  |

## Readout

- Positive in this batch: `ReClor` (+1/12) and `BBH formal_fallacies` (+1/12).
- Neutral: `BBH navigate` stayed 10/12 because baseline was already high.
- Negative: `BBH disambiguation_qa`, `reasoning_about_colored_objects`, and `penguins_in_a_table` each dropped by 1/12 with the current structured wording.
- Batch total is slightly negative: 42/72 -> 41/72.

## Dataset Sources

- BBH: https://huggingface.co/datasets/lukaemon/bbh
- LSAT-AR: https://huggingface.co/datasets/hails/agieval-lsat-ar
- ProntoQA: https://huggingface.co/datasets/renma/ProntoQA
- ReClor: https://huggingface.co/datasets/hadithya369/ReClor
