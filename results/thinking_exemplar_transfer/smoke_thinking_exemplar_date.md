# Thinking-Exemplar Transfer: BBH date_understanding

- Run id: `smoke_thinking_exemplar_date`
- Model: `Qwen/Qwen3.5-4B`
- Exemplar generation: `enable_thinking=True`
- Evaluation generation: `enable_thinking=False`
- Exemplar row: `20`
- Eval window: offset `21`, limit `2`
- Exemplar parsed answer: `B`; gold: `B`; correct: `True`

## Accuracy

| Condition | Correct | Accuracy |
|---|---:|---:|
| none | 2/2 | 100.0% |
| thinking_exemplar | 2/2 | 100.0% |
| delta | +0 | +0.0% |

## Movement

- Recovered: `-`
- Harmed: `-`

## Artifacts

- Exemplar thinking JSON: `results/thinking_exemplar_transfer/smoke_thinking_exemplar_date_exemplar.json`
- Raw evaluation JSONL: `results/thinking_exemplar_transfer/smoke_thinking_exemplar_date.jsonl`
