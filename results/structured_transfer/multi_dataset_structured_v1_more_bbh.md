# Structured Transfer Eval

- Run id: `multi_dataset_structured_v1_more_bbh`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Levels: `none, structured`
- Eval offset: `20`
- Limit per dataset: `12`

| Dataset | Source | None | Structured | Delta | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `bbh_date` | lukaemon/bbh:date_understanding | 5/12 (41.7%) | 7/12 (58.3%) | +2 | 2/7 | 0/5 |
| `bbh_temporal` | lukaemon/bbh:temporal_sequences | 11/12 (91.7%) | 11/12 (91.7%) | +0 | 0/1 | 0/11 |

## Dataset Notes

### `bbh_date`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: First few date-understanding examples: identify anchor date, requested offset, and output format.
- Recovered rows: 21, 25
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | B | B |
| 21 | B | A | B |
| 22 | D | A | A |
| 23 | C | B | D |
| 24 | A | A | A |
| 25 | D | A | D |
| 26 | F | F | F |
| 27 | B | A | E |
| 28 | F | B | B |
| 29 | D | D | D |
| 30 | E | E | E |
| 31 | C | A | A |

### `bbh_temporal`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: First few temporal-sequence examples: mark occupied time intervals and compare options to the free interval.
- Recovered rows: -
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | B | B |
| 21 | D | D | D |
| 22 | A | A | A |
| 23 | D | D | D |
| 24 | B | B | B |
| 25 | A | A | A |
| 26 | B | B | B |
| 27 | D | D | D |
| 28 | D | D | D |
| 29 | B | C | C |
| 30 | A | A | A |
| 31 | C | C | C |

## Guardrail

Structured hints are generated from question text only. They list task structure, entities, clue sentences, option maps, and reusable procedures, but do not compute final target candidates or answer letters.
