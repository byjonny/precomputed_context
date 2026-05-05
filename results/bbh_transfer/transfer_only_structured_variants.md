# BBH Transfer-Only Structured Hint Variants

This summary excludes per-example solved context from the main comparison. All transfer-only variants are prompt templates learned from earlier BBH logical-deduction examples and then instantiated on held-out questions using only question text.

## First 20 Held-Out Rows

| Variant | Structured hint shape | None | Structured | Net | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `v1` | light fact grouping: items/target/fixed facts/comparison facts | 12/20 | 14/20 | +2 | 2/8 | 0/12 |
| `v6` | v1-style grouping plus explicit seven-slot protocol | 12/20 | 14/20 | +2 | 2/8 | 0/12 |
| `v7` | compact items/target/all-clues table scaffold | 12/20 | 14/20 | +2 | 2/8 | 0/12 |
| `v8` | normalized scale + fixed/pairwise constraints, no solver | 12/20 | 14/20 | +2 | 2/8 | 0/12 |
| `v9` | failure-proofing wording: avoid endpoints/defaults, propagate chains | 12/20 | 14/20 | +2 | 2/8 | 0/12 |
| `v10` | option-check wording + option label map, no solver | 12/20 | 14/20 | +2 | 2/8 | 0/12 |
| `v11` | empty-slot/elimination wording + option label map | 12/20 | 13/20 | +1 | 2/8 | 1/12 |
| `v12` | compact label map + full clue list checklist | 12/20 | 13/20 | +1 | 2/8 | 1/12 |

## Full 37 Held-Out Rows

| Variant | Structured hint shape | None | Structured | Net | None-wrong recovered | None-correct harmed | Recovered rows | Harmed rows |
|---|---|---:|---:|---:|---:|---:|---|---|
| `v1` | light fact grouping: items/target/fixed facts/comparison facts | 21/37 | 24/37 | +3 | 3/16 | 0/21 | 214, 227, 248 | - |
| `v9` | failure-proofing wording: avoid endpoints/defaults, propagate chains | 21/37 | 23/37 | +2 | 3/16 | 1/21 | 214, 227, 248 | 237 |
| `v10` | option-check wording + option label map, no solver | 21/37 | 24/37 | +3 | 4/16 | 1/21 | 214, 227, 241, 248 | 237 |

## Non-Transfer Upper Bound

| Variant | Context type | None | Structured | Net | Note |
|---|---|---:|---:|---:|---|
| `v5` | NOT transfer-only: normalized constraints + target-slot propagation | 21/37 | 37/37 | +16 | Excluded from transferability conclusion because it computes possible target-slot item(s) per question. |

## Takeaway

- Best transfer-only result so far is still effectively `v1`: 24/37 versus 21/37 baseline, with no harm to originally correct cases.
- Rewording structured hints changed error modes but did not improve net transfer accuracy. `v10` rescued one extra baseline-wrong row, but also damaged one baseline-correct row.
- The large jump from `v5` shows the model can use richer precomputed context, but that context is per-example constraint propagation rather than transferable hint wording.
