# Hint Lab Summary

- Run id: `ladder_more_01_bbh209_fix`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Repeats per level: `2`
- Levels: `exact, near_exact`

| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable | Failure boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `bbh_209_golf_third_last` | bbh_logical_deduction | A | G | 2/2 (G) | 0/2 (B) | not run | not run | not run | exact | near_exact |

## Per-Case Notes

### `bbh_209_golf_third_last`

- Gold: `G`
- Prior baseline: raw `A`, parsed `A`
- `exact`: r1='G', r2='G'
- `near_exact`: r1='B', r2='B'
