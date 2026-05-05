# BBH Transfer Eval v1 Combined Heldout 37

- Combined files: `v1_heldout20.jsonl` + `v1_heldout17b.jsonl`
- Held-out rows: 213-249, excluding earlier BBH hint-lab train rows by construction.

| Level | Accuracy | Delta vs none | None-wrong recovered | None-correct preserved |
|---|---:|---:|---:|---:|
| `none` | 21/37 (56.8%) | +0.0% | n/a | n/a |
| `structured` | 24/37 (64.9%) | +8.1% | 3/16 | 21/21 |
| `generalized` | 22/37 (59.5%) | +2.7% | 3/16 | 19/21 |
| `minimal` | 20/37 (54.1%) | -2.7% | 0/16 | 20/21 |

## None-wrong Rows

| Row | Gold | None | Structured | Generalized | Minimal |
|---:|---:|---:|---:|---:|---:|
| 214 | C | A | C | G | G |
| 216 | D | A | A | G | G |
| 218 | D | A | A | A | E |
| 222 | C | A | A | A | G |
| 226 | B | G | A | E | G |
| 227 | C | G | C | C | G |
| 228 | E | A | A | A | A |
| 231 | F | G | G | G | G |
| 233 | C | A | A | A | A |
| 234 | B | A | A | A | A |
| 236 | F | A | A | A | A |
| 240 | E | A | A | A | A |
| 241 | G | D | D | G | D |
| 242 | F | G | G | A | A |
| 246 | D | G | A | G | A |
| 248 | F | A | F | F | G |