# Combined Hint Lab Summary

- Repeats per level: `2`
- Includes `ladder_initial`, `ladder_more_01`, and `ladder_more_01_bbh209_fix` overlay.

| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `bbh_34_fruit_prices` | bbh_logical_deduction | A | G | 2/2 (G,G) | 0/2 (B,B) | 0/2 (B,B) | 2/2 (G,G) | 2/2 (G,G) | minimal |
| `bbh_212_golf_first` | bbh_logical_deduction | A | G | 2/2 (G,G) | 0/2 (A,A) | 0/2 (A,A) | 2/2 (G,G) | 2/2 (G,G) | minimal |
| `lsat_61_bicycle_except` | lsat_ar | E | D | 2/2 (D,D) | 2/2 (D,D) | 0/2 (E,E) | 0/2 (E,E) | 0/2 (E,E) | near_exact |
| `lsat_200_antique_auction` | lsat_ar | A | B | 2/2 (B,B) | 0/2 (A,A) | 0/2 (E,E) | 0/2 (E,E) | 0/2 (E,E) | exact |
| `prontoqa_416_polly_opaque` | prontoqa | A | B | 2/2 (B,B) | 0/2 (A,A) | 0/2 (A,A) | 0/2 (A,A) | 0/2 (A,A) | exact |
| `prontoqa_326_alex_transparent` | prontoqa | B | A | 2/2 (A,A) | 2/2 (A,A) | 2/2 (A,A) | 0/2 (B,B) | 0/2 (B,B) | structured |
| `bbh_54_golf_fourth` | bbh_logical_deduction | A | B | 2/2 (B,B) | 0/2 (A,A) | 0/2 (A,A) | 0/2 (G,G) | 0/2 (A,A) | exact |
| `bbh_99_car_third_oldest` | bbh_logical_deduction | A | D | 2/2 (D,D) | 0/2 (A,A) | 0/2 (A,A) | 0/2 (A,A) | 0/2 (A,A) | exact |
| `bbh_209_golf_third_last` | bbh_logical_deduction | A | G | 2/2 (G,G) | 0/2 (B,B) | 0/2 (B,B) | 2/2 (G,G) | 2/2 (G,G) | minimal |
| `lsat_222_art_wall` | lsat_ar | A | B | 2/2 (B,B) | 2/2 (B,B) | 0/2 (A,A) | 0/2 (A,A) | 0/2 (E,E) | near_exact |
| `lsat_62_bicycle_cannot` | lsat_ar | A | C | 2/2 (C,C) | 2/2 (C,C) | 2/2 (C,C) | 0/2 (E,E) | 0/2 (E,E) | structured |
| `lsat_171_photo_sections` | lsat_ar | A | C | 2/2 (C,C) | 2/2 (C,C) | 0/2 (A,A) | 0/2 (A,A) | 0/2 (A,A) | near_exact |

## Notes

- Success is strict 2/2 at temperature 0.
- Several cases are non-monotonic: a more detailed middle representation can fail while a minimal strategy succeeds.
- Exact hints now rescue all 12 selected baseline-wrong cases.