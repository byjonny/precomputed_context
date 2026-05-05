# Context Evaluation Summary

- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Seed: `20260424`
- Max tokens per generation: `16`
- Target qualified examples per dataset: `1`

### bbh_logical_deduction

- Processed examples: 1
- Qualified examples: 0 (0.0%)
- None-wrong pool: 1

| Hint level | Full-sample accuracy | Qualified-set accuracy | Recovery from none-wrong |
|---|---:|---:|---:|
| `none` | 0/1 (0.0%) | n/a | n/a |
| `generic_hint` | 0/1 (0.0%) | n/a | 0/1 (0.0%) |
| `structured_hint` | 0/1 (0.0%) | n/a | 0/1 (0.0%) |
| `guided_hint` | 0/1 (0.0%) | n/a | 0/1 (0.0%) |

### lsat_ar

- Processed examples: 1
- Qualified examples: 0 (0.0%)
- None-wrong pool: 1

| Hint level | Full-sample accuracy | Qualified-set accuracy | Recovery from none-wrong |
|---|---:|---:|---:|
| `none` | 0/1 (0.0%) | n/a | n/a |
| `generic_hint` | 0/1 (0.0%) | n/a | 0/1 (0.0%) |
| `structured_hint` | 0/1 (0.0%) | n/a | 0/1 (0.0%) |
| `guided_hint` | 0/1 (0.0%) | n/a | 0/1 (0.0%) |

### prontoqa

- Processed examples: 1
- Qualified examples: 0 (0.0%)
- None-wrong pool: 0

| Hint level | Full-sample accuracy | Qualified-set accuracy | Recovery from none-wrong |
|---|---:|---:|---:|
| `none` | 1/1 (100.0%) | n/a | n/a |
| `generic_hint` | 1/1 (100.0%) | n/a | 0/0 (n/a) |
| `structured_hint` | 0/1 (0.0%) | n/a | 0/0 (n/a) |
| `guided_hint` | 1/1 (100.0%) | n/a | 0/0 (n/a) |

## Prompt Audit

The raw JSONL includes `hint` and `user_prompt` for every call. Use those fields to spot-check that hints do not directly state the gold letter.
