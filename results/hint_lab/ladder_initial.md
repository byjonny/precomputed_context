# Hint Lab Summary

- Run id: `ladder_initial`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Repeats per level: `2`
- Levels: `none, exact, near_exact, structured, generalized, minimal`

| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable | Failure boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `bbh_34_fruit_prices` | bbh_logical_deduction | A | G | 2/2 (G) | 0/2 (B) | 0/2 (B) | 2/2 (G) | 2/2 (G) | minimal | no more-general level in this run |
| `bbh_212_golf_first` | bbh_logical_deduction | A | G | 2/2 (G) | 0/2 (A) | 0/2 (A) | 2/2 (G) | 2/2 (G) | minimal | no more-general level in this run |
| `lsat_61_bicycle_except` | lsat_ar | E | D | 2/2 (D) | 2/2 (D) | 0/2 (E) | 0/2 (E) | 0/2 (E) | near_exact | structured |
| `lsat_200_antique_auction` | lsat_ar | A | B | 2/2 (B) | 0/2 (A) | 0/2 (E) | 0/2 (E) | 0/2 (E) | exact | near_exact |
| `prontoqa_416_polly_opaque` | prontoqa | A | B | 2/2 (B) | 0/2 (A) | 0/2 (A) | 0/2 (A) | 0/2 (A) | exact | near_exact |
| `prontoqa_326_alex_transparent` | prontoqa | B | A | 2/2 (A) | 2/2 (A) | 2/2 (A) | 0/2 (B) | 0/2 (B) | structured | generalized |

## Per-Case Notes

### `bbh_34_fruit_prices`

- Gold: `G`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='G', r2='G'
- `near_exact`: r1='B', r2='B'
- `structured`: r1='B', r2='B'
- `generalized`: r1='G', r2='G'
- `minimal`: r1='G', r2='G'

### `bbh_212_golf_first`

- Gold: `G`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='G', r2='G'
- `near_exact`: r1='A', r2='A'
- `structured`: r1='A', r2='A'
- `generalized`: r1='G', r2='G'
- `minimal`: r1='G', r2='G'

### `lsat_61_bicycle_except`

- Gold: `D`
- Prior baseline: raw `E`, parsed `E`
- `none`: r1='E', r2='E'
- `exact`: r1='D', r2='D'
- `near_exact`: r1='D', r2='D'
- `structured`: r1='E', r2='E'
- `generalized`: r1='E', r2='E'
- `minimal`: r1='E', r2='E'

### `lsat_200_antique_auction`

- Gold: `B`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='E', r2='E'
- `exact`: r1='B', r2='B'
- `near_exact`: r1='A', r2='A'
- `structured`: r1='E', r2='E'
- `generalized`: r1='E', r2='E'
- `minimal`: r1='E', r2='E'

### `prontoqa_416_polly_opaque`

- Gold: `B`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='B', r2='B'
- `near_exact`: r1='A', r2='A'
- `structured`: r1='A', r2='A'
- `generalized`: r1='A', r2='A'
- `minimal`: r1='A', r2='A'

### `prontoqa_326_alex_transparent`

- Gold: `A`
- Prior baseline: raw `B`, parsed `B`
- `none`: r1='B', r2='B'
- `exact`: r1='A', r2='A'
- `near_exact`: r1='A', r2='A'
- `structured`: r1='A', r2='A'
- `generalized`: r1='B', r2='B'
- `minimal`: r1='B', r2='B'
