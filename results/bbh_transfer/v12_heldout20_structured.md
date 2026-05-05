# BBH Transfer Eval (v12)

- Dataset: `lukaemon/bbh`, config `logical_deduction_seven_objects`
- Test split: held-out row ids after the BBH hint-lab examples
- Model: `Qwen/Qwen3.5-4B`, `enable_thinking=False`, temperature 0

| Level | Accuracy | Delta vs none | None-wrong recovered | None-correct preserved |
|---|---:|---:|---:|---:|
| `none` | 12/20 (60.0%) | +0.0% | n/a | n/a |
| `structured` | 13/20 (65.0%) | +5.0% | 2/8 | 11/12 |

## Per-Example Outputs

| Row | Gold | None | Structured | Generalized | Minimal |
|---:|---:|---:|---:|---:|---:|
| 213 | F | F | F | None | None |
| 214 | C | A | C | None | None |
| 215 | D | D | D | None | None |
| 216 | D | A | A | None | None |
| 217 | B | B | B | None | None |
| 218 | D | A | E | None | None |
| 219 | A | A | E | None | None |
| 220 | G | G | G | None | None |
| 221 | B | B | B | None | None |
| 222 | C | A | A | None | None |
| 223 | G | G | G | None | None |
| 224 | D | D | D | None | None |
| 225 | F | F | F | None | None |
| 226 | B | G | G | None | None |
| 227 | C | G | C | None | None |
| 228 | E | A | C | None | None |
| 229 | E | E | E | None | None |
| 230 | F | F | F | None | None |
| 231 | F | G | G | None | None |
| 232 | G | G | G | None | None |
