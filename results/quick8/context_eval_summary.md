# Context Evaluation Summary

- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Seed: `20260424`
- Max tokens per generation: `16`
- Target qualified examples per dataset: `3`

### bbh_logical_deduction

- Processed examples: 8
- Qualified examples: 2 (25.0%)
- None-wrong pool: 5

| Hint level | Full-sample accuracy | Qualified-set accuracy | Recovery from none-wrong |
|---|---:|---:|---:|
| `none` | 3/8 (37.5%) | 0.0% | n/a |
| `generic_hint` | 5/8 (62.5%) | 100.0% | 2/5 (40.0%) |
| `structured_hint` | 4/8 (50.0%) | 50.0% | 1/5 (20.0%) |
| `guided_hint` | 5/8 (62.5%) | 100.0% | 2/5 (40.0%) |

Qualified example ids, first 10:
- `bbh_logical_deduction::bbh_logical_deduction_seven_objects::212`
- `bbh_logical_deduction::bbh_logical_deduction_seven_objects::34`

### lsat_ar

- Processed examples: 8
- Qualified examples: 0 (0.0%)
- None-wrong pool: 7

| Hint level | Full-sample accuracy | Qualified-set accuracy | Recovery from none-wrong |
|---|---:|---:|---:|
| `none` | 1/8 (12.5%) | n/a | n/a |
| `generic_hint` | 0/8 (0.0%) | n/a | 0/7 (0.0%) |
| `structured_hint` | 0/8 (0.0%) | n/a | 0/7 (0.0%) |
| `guided_hint` | 0/8 (0.0%) | n/a | 0/7 (0.0%) |

### prontoqa

- Processed examples: 8
- Qualified examples: 0 (0.0%)
- None-wrong pool: 2

| Hint level | Full-sample accuracy | Qualified-set accuracy | Recovery from none-wrong |
|---|---:|---:|---:|
| `none` | 6/8 (75.0%) | n/a | n/a |
| `generic_hint` | 6/8 (75.0%) | n/a | 0/2 (0.0%) |
| `structured_hint` | 5/8 (62.5%) | n/a | 0/2 (0.0%) |
| `guided_hint` | 6/8 (75.0%) | n/a | 0/2 (0.0%) |

## Prompt Audit

The raw JSONL includes `hint` and `user_prompt` for every call. Use those fields to spot-check that hints do not directly state the gold letter.
