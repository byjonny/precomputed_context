# BBH Transfer Eval (v9)

- Dataset: `lukaemon/bbh`, config `logical_deduction_seven_objects`
- Test split: held-out row ids after the BBH hint-lab examples
- Model: `Qwen/Qwen3.5-4B`, `enable_thinking=False`, temperature 0

| Level | Accuracy | Delta vs none | None-wrong recovered | None-correct preserved |
|---|---:|---:|---:|---:|
| `none` | 9/17 (52.9%) | +0.0% | n/a | n/a |
| `structured` | 9/17 (52.9%) | +0.0% | 1/8 | 8/9 |

## Per-Example Outputs

| Row | Gold | None | Structured | Generalized | Minimal |
|---:|---:|---:|---:|---:|---:|
| 233 | C | A | G | None | None |
| 234 | B | A | G | None | None |
| 235 | A | A | A | None | None |
| 236 | F | A | A | None | None |
| 237 | A | A | G | None | None |
| 238 | F | F | F | None | None |
| 239 | F | F | F | None | None |
| 240 | E | A | A | None | None |
| 241 | G | D | D | None | None |
| 242 | F | G | G | None | None |
| 243 | C | C | C | None | None |
| 244 | C | C | C | None | None |
| 245 | A | A | A | None | None |
| 246 | D | G | G | None | None |
| 247 | A | A | A | None | None |
| 248 | F | A | F | None | None |
| 249 | D | D | D | None | None |
