# Hint Lab Summary

- Run id: `smoke_pronto416_exact_v2`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Repeats per level: `2`
- Levels: `exact`

| Case | Dataset | Baseline | Gold | Exact | Near exact | Structured | Generalized | Minimal | Most general stable | Failure boundary |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `prontoqa_416_polly_opaque` | prontoqa | A | B | 2/2 (B) | not run | not run | not run | not run | exact | no more-general level in this run |

## Per-Case Notes

### `prontoqa_416_polly_opaque`

- Gold: `B`
- Prior baseline: raw `A`, parsed `A`
- `exact`: r1='B', r2='B'
