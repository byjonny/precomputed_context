# Hint Lab Summary

- Run id: `smoke_core`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Repeats per level: `2`
- Levels: `none, exact`

| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable | Failure boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `bbh_34_fruit_prices` | bbh_logical_deduction | A | G | 2/2 (G) | not run | not run | not run | not run | exact | no more-general level in this run |
| `lsat_61_bicycle_except` | lsat_ar | E | D | 2/2 (D) | not run | not run | not run | not run | exact | no more-general level in this run |
| `prontoqa_416_polly_opaque` | prontoqa | A | B | 0/2 (A) | not run | not run | not run | not run | none | exact failed or was not run |

## Per-Case Notes

### `bbh_34_fruit_prices`

- Gold: `G`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='G', r2='G'

### `lsat_61_bicycle_except`

- Gold: `D`
- Prior baseline: raw `E`, parsed `E`
- `none`: r1='E', r2='E'
- `exact`: r1='D', r2='D'

### `prontoqa_416_polly_opaque`

- Gold: `B`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='A', r2='A'
