# BBH Structured Hint Variants Combined

| Variant | Structured style | None accuracy | Structured accuracy | Delta | None-wrong recovered | None-correct preserved |
|---|---|---:|---:|---:|---:|---:|
| `v1` | light automatic fact grouping | 21/37 (56.8%) | 24/37 (64.9%) | +8.1% | 3/16 | 21/21 |
| `v5` | normalized constraints + target-slot propagation | 21/37 (56.8%) | 37/37 (100.0%) | +43.2% | 16/16 | 21/21 |

## Notes

- `v1` keeps structured context light: extracted items, target phrase, fixed/ordinal facts, comparison facts.
- `v5` is stronger: it normalizes constraints, runs target-slot propagation, and gives possible item(s) for the target slot, but still never writes the final answer letter.
- Held-out rows: 213-249 from BBH logical_deduction_seven_objects.