# Structured Transfer Eval

- Run id: `new_dataset_structured_v1_reclor`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Levels: `none, structured`
- Eval offset: `20`
- Limit per dataset: `12`

| Dataset | Source | None | Structured | Delta | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `reclor` | hadithya369/ReClor:validation | 8/12 (66.7%) | 9/12 (75.0%) | +1 | 2/4 | 1/8 |

## Dataset Notes

### `reclor`

- Dataset URL: https://huggingface.co/datasets/hadithya369/ReClor
- Template seed: First few ReClor logical-reading examples: separate argument, question task, and answer-choice roles.
- Recovered rows: val_28, val_30
- Harmed rows: val_25

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| val_20 | B | B | B |
| val_21 | D | A | A |
| val_22 | D | D | D |
| val_23 | B | B | B |
| val_24 | D | D | D |
| val_25 | D | D | C |
| val_26 | C | C | C |
| val_27 | C | C | C |
| val_28 | C | D | C |
| val_29 | B | D | D |
| val_30 | A | D | A |
| val_31 | B | B | B |

## Guardrail

Structured hints are generated from question text only. They list task structure, entities, clue sentences, option maps, and reusable procedures, but do not compute final target candidates or answer letters.
