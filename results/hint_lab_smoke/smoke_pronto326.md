# Hint Lab Summary

- Run id: `smoke_pronto326`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Repeats per level: `2`
- Levels: `none, exact`

| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable | Failure boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `prontoqa_326_alex_transparent` | prontoqa | B | A | 2/2 (A) | not run | not run | not run | not run | exact | no more-general level in this run |

## Per-Case Notes

### `prontoqa_326_alex_transparent`

- Gold: `A`
- Prior baseline: raw `B`, parsed `B`
- `none`: r1='B', r2='B'
- `exact`: r1='A', r2='A'
