# Thinking-Exemplar Transfer: BBH date_understanding

- Run id: `date_thinking_exemplar_v2_fixed_answer`
- Model: `Qwen/Qwen3.5-4B`
- Exemplar generation: `enable_thinking=True`
- Evaluation generation: `enable_thinking=False`
- Exemplar row: `20`
- Eval window: offset `21`, limit `50`
- Exemplar parsed answer: `B`; gold: `B`; correct: `True`

## Accuracy

| Condition | Correct | Accuracy |
|---|---:|---:|
| none | 35/50 | 70.0% |
| thinking_exemplar | 27/50 | 54.0% |
| delta | -8 | -16.0% |

## Movement

- Recovered: `27, 33`
- Harmed: `24, 26, 30, 40, 46, 47, 57, 61, 64, 67`

## Artifacts

- Exemplar thinking JSON: `results/thinking_exemplar_transfer/date_thinking_exemplar_v2_fixed_answer_exemplar.json`
- Raw evaluation JSONL: `results/thinking_exemplar_transfer/date_thinking_exemplar_v2_fixed_answer.jsonl`
