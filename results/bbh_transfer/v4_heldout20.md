# BBH Transfer Eval (v4)

- Dataset: `lukaemon/bbh`, config `logical_deduction_seven_objects`
- Test split: held-out row ids after the BBH hint-lab examples
- Model: `Qwen/Qwen3.5-4B`, `enable_thinking=False`, temperature 0

| Level | Accuracy | Delta vs none | None-wrong recovered | None-correct preserved |
|---|---:|---:|---:|---:|
| `none` | 12/20 (60.0%) | +0.0% | n/a | n/a |
| `structured` | 13/20 (65.0%) | +5.0% | 2/8 | 11/12 |
| `generalized` | 12/20 (60.0%) | +0.0% | 1/8 | 11/12 |
| `minimal` | 11/20 (55.0%) | -5.0% | 0/8 | 11/12 |

## Per-Example Outputs

| Row | Gold | None | Structured | Generalized | Minimal |
|---:|---:|---:|---:|---:|---:|
| 213 | F | F | F | F | F |
| 214 | C | A | C | G | G |
| 215 | D | D | D | D | D |
| 216 | D | A | A | G | G |
| 217 | B | B | B | B | B |
| 218 | D | A | A | A | E |
| 219 | A | A | A | A | A |
| 220 | G | G | G | G | G |
| 221 | B | B | B | B | B |
| 222 | C | A | A | A | G |
| 223 | G | G | G | G | G |
| 224 | D | D | E | E | D |
| 225 | F | F | F | F | F |
| 226 | B | G | E | E | G |
| 227 | C | G | C | C | G |
| 228 | E | A | A | A | A |
| 229 | E | E | E | E | E |
| 230 | F | F | F | F | F |
| 231 | F | G | G | G | G |
| 232 | G | G | G | G | A |
