# BBH Transfer Eval (v1)

- Dataset: `lukaemon/bbh`, config `logical_deduction_seven_objects`
- Test split: held-out row ids after the BBH hint-lab examples
- Model: `Qwen/Qwen3.5-4B`, `enable_thinking=False`, temperature 0

| Level | Accuracy | Delta vs none | None-wrong recovered | None-correct preserved |
|---|---:|---:|---:|---:|
| `none` | 9/17 (52.9%) | +0.0% | n/a | n/a |
| `structured` | 10/17 (58.8%) | +5.9% | 1/8 | 9/9 |
| `generalized` | 10/17 (58.8%) | +5.9% | 2/8 | 8/9 |
| `minimal` | 9/17 (52.9%) | +0.0% | 0/8 | 9/9 |

## Per-Example Outputs

| Row | Gold | None | Structured | Generalized | Minimal |
|---:|---:|---:|---:|---:|---:|
| 233 | C | A | A | A | A |
| 234 | B | A | A | A | A |
| 235 | A | A | A | A | A |
| 236 | F | A | A | A | A |
| 237 | A | A | A | A | A |
| 238 | F | F | F | F | F |
| 239 | F | F | F | F | F |
| 240 | E | A | A | A | A |
| 241 | G | D | D | G | D |
| 242 | F | G | G | A | A |
| 243 | C | C | C | E | C |
| 244 | C | C | C | C | C |
| 245 | A | A | A | A | A |
| 246 | D | G | A | G | A |
| 247 | A | A | A | A | A |
| 248 | F | A | F | F | G |
| 249 | D | D | D | D | D |
