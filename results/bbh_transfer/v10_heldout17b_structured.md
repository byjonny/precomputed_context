# BBH Transfer Eval (v10)

- Dataset: `lukaemon/bbh`, config `logical_deduction_seven_objects`
- Test split: held-out row ids after the BBH hint-lab examples
- Model: `Qwen/Qwen3.5-4B`, `enable_thinking=False`, temperature 0

| Level | Accuracy | Delta vs none | None-wrong recovered | None-correct preserved |
|---|---:|---:|---:|---:|
| `none` | 9/17 (52.9%) | +0.0% | n/a | n/a |
| `structured` | 10/17 (58.8%) | +5.9% | 2/8 | 8/9 |

## Per-Example Outputs

| Row | Gold | None | Structured | Generalized | Minimal |
|---:|---:|---:|---:|---:|---:|
| 233 | C | A | A | None | None |
| 234 | B | A | G | None | None |
| 235 | A | A | A | None | None |
| 236 | F | A | E | None | None |
| 237 | A | A | G | None | None |
| 238 | F | F | F | None | None |
| 239 | F | F | F | None | None |
| 240 | E | A | D | None | None |
| 241 | G | D | G | None | None |
| 242 | F | G | G | None | None |
| 243 | C | C | C | None | None |
| 244 | C | C | C | None | None |
| 245 | A | A | A | None | None |
| 246 | D | G | A | None | None |
| 247 | A | A | A | None | None |
| 248 | F | A | F | None | None |
| 249 | D | D | D | None | None |
