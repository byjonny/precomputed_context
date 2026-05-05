# Hint Lab Summary

- Run id: `ladder_more_01`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Repeats per level: `2`
- Levels: `none, exact, near_exact, structured, generalized, minimal`

| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable | Failure boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `bbh_54_golf_fourth` | bbh_logical_deduction | A | B | 2/2 (B) | 0/2 (A) | 0/2 (A) | 0/2 (G) | 0/2 (A) | exact | near_exact |
| `bbh_99_car_third_oldest` | bbh_logical_deduction | A | D | 2/2 (D) | 0/2 (A) | 0/2 (A) | 0/2 (A) | 0/2 (A) | exact | near_exact |
| `bbh_209_golf_third_last` | bbh_logical_deduction | A | G | 0/2 (A) | 0/2 (B) | 0/2 (B) | 2/2 (G) | 2/2 (G) | minimal | no more-general level in this run |
| `lsat_222_art_wall` | lsat_ar | A | B | 2/2 (B) | 2/2 (B) | 0/2 (A) | 0/2 (A) | 0/2 (E) | near_exact | structured |
| `lsat_62_bicycle_cannot` | lsat_ar | A | C | 2/2 (C) | 2/2 (C) | 2/2 (C) | 0/2 (E) | 0/2 (E) | structured | generalized |
| `lsat_171_photo_sections` | lsat_ar | A | C | 2/2 (C) | 2/2 (C) | 0/2 (A) | 0/2 (A) | 0/2 (A) | near_exact | structured |

## Per-Case Notes

### `bbh_54_golf_fourth`

- Gold: `B`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='B', r2='B'
- `near_exact`: r1='A', r2='A'
- `structured`: r1='A', r2='A'
- `generalized`: r1='G', r2='G'
- `minimal`: r1='A', r2='A'

### `bbh_99_car_third_oldest`

- Gold: `D`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='D', r2='D'
- `near_exact`: r1='A', r2='A'
- `structured`: r1='A', r2='A'
- `generalized`: r1='A', r2='A'
- `minimal`: r1='A', r2='A'

### `bbh_209_golf_third_last`

- Gold: `G`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='A', r2='A'
- `near_exact`: r1='B', r2='B'
- `structured`: r1='B', r2='B'
- `generalized`: r1='G', r2='G'
- `minimal`: r1='G', r2='G'

### `lsat_222_art_wall`

- Gold: `B`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='B', r2='B'
- `near_exact`: r1='B', r2='B'
- `structured`: r1='A', r2='A'
- `generalized`: r1='A', r2='A'
- `minimal`: r1='E', r2='E'

### `lsat_62_bicycle_cannot`

- Gold: `C`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='C', r2='C'
- `near_exact`: r1='C', r2='C'
- `structured`: r1='C', r2='C'
- `generalized`: r1='E', r2='E'
- `minimal`: r1='E', r2='E'

### `lsat_171_photo_sections`

- Gold: `C`
- Prior baseline: raw `A`, parsed `A`
- `none`: r1='A', r2='A'
- `exact`: r1='C', r2='C'
- `near_exact`: r1='C', r2='C'
- `structured`: r1='A', r2='A'
- `generalized`: r1='A', r2='A'
- `minimal`: r1='A', r2='A'
