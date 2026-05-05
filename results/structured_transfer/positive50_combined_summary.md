# Positive Candidate 50-Example Structured Transfer Summary

- Model: `Qwen/Qwen3.5-4B` via `mlx_lm`
- Thinking mode: `enable_thinking=False`; temperature `0`; answer constrained to one letter
- Levels: `none` vs `structured`; 50 examples per dataset/config
- Structured boundary: reusable template + question-text extraction only; no final candidate propagation or answer-letter computation

| Dataset/config | Window | Hint shape | None | Structured | Delta | Recovered | Harmed |
|---|---|---|---:|---:|---:|---:|---:|
| `BBH date_understanding` | offset 20, rows 20-69 | date anchor + offset + format | 32/50 (64.0%) | 38/50 (76.0%) | +6 | 7/18 | 1/32 |
| `ProntoQA` | offset 20, ProntoQA_21-70 | forward-chain rule inventory | 35/50 (70.0%) | 39/50 (78.0%) | +4 | 4/15 | 0/35 |
| `ReClor validation` | offset 20, val_20-69 | logical-reading argument roles | 37/50 (74.0%) | 36/50 (72.0%) | -1 | 3/13 | 4/37 |
| `BBH formal_fallacies` | offset 20, rows 20-69 | premise/conclusion validity | 28/50 (56.0%) | 31/50 (62.0%) | +3 | 7/22 | 4/28 |
| `ProofWriter validation` | offset 20, rows 20-69 | facts/rules/query forward-chain | 29/50 (58.0%) | 31/50 (62.0%) | +2 | 5/21 | 3/29 |
| `WinoGrande debiased validation` | offset 20, rows 20-69 | blank/candidate semantic role | 37/50 (74.0%) | 38/50 (76.0%) | +1 | 3/13 | 2/37 |
| `BBH logical_deduction_seven_objects` | offset 150, rows 150-199; chosen to avoid earlier hint-lab rows | ordering fact grouping | 30/50 (60.0%) | 31/50 (62.0%) | +1 | 4/20 | 3/30 |
| **Total** |  |  | **228/350 (65.1%)** | **244/350 (69.7%)** | **+16** |  |  |

## Readout

- Expanded 7 previously positive candidates to 50 examples each: 228/350 -> 244/350, net `+16`.
- The strongest retained gains are `BBH date_understanding` (+6), `ProntoQA` (+4), and `BBH formal_fallacies` (+3).
- `ProofWriter`, `WinoGrande`, and `BBH logical_deduction_seven_objects` remain slightly positive at +2, +1, and +1.
- `ReClor` did not hold its 12-example gain: it moved from +1 in the small run to -1 over 50 examples.
- `ProntoQA` is the cleanest gain in this batch: +4 with zero harmed baseline-correct examples.

## Raw Result Files

- `results/structured_transfer/positive50_structured_v1.jsonl`
- `results/structured_transfer/positive50_bbh_logical_seven_v1.jsonl`
