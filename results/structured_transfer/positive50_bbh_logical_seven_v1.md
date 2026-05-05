# Structured Transfer Eval

- Run id: `positive50_bbh_logical_seven_v1`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Levels: `none, structured`
- Eval offset: `150`
- Limit per dataset: `50`

| Dataset | Source | None | Structured | Delta | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `bbh_logical_seven` | lukaemon/bbh:logical_deduction_seven_objects | 30/50 (60.0%) | 31/50 (62.0%) | +1 | 4/20 | 3/30 |

## Dataset Notes

### `bbh_logical_seven`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: Earlier BBH logical-deduction examples used for v1/v6 transfer templates.
- Recovered rows: 167, 173, 177, 194
- Harmed rows: 164, 179, 181

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 150 | D | D | D |
| 151 | C | C | C |
| 152 | C | C | C |
| 153 | F | A | G |
| 154 | C | A | G |
| 155 | E | A | F |
| 156 | B | B | B |
| 157 | C | A | B |
| 158 | B | A | A |
| 159 | E | A | B |
| 160 | E | E | E |
| 161 | A | A | A |
| 162 | F | F | F |
| 163 | E | A | A |
| 164 | A | A | D |
| 165 | B | B | B |
| 166 | C | C | C |
| 167 | G | A | G |
| 168 | F | F | F |
| 169 | C | C | C |
| 170 | A | A | A |
| 171 | C | C | C |
| 172 | A | A | A |
| 173 | E | G | E |
| 174 | F | F | F |
| 175 | G | G | G |
| 176 | F | G | G |
| 177 | F | A | F |
| 178 | A | A | A |
| 179 | B | B | C |
| 180 | G | G | G |
| 181 | A | A | B |
| 182 | C | B | B |
| 183 | B | B | B |
| 184 | D | G | G |
| 185 | A | A | A |
| 186 | G | G | G |
| 187 | B | A | A |
| 188 | C | C | C |
| 189 | B | G | G |
| 190 | B | B | B |
| 191 | E | G | G |
| 192 | E | E | E |
| 193 | C | A | A |
| 194 | G | A | G |
| 195 | C | G | G |
| 196 | D | D | D |
| 197 | E | E | E |
| 198 | B | A | G |
| 199 | D | D | D |

## Guardrail

Structured hints are generated from question text only. They list task structure, entities, clue sentences, option maps, and reusable procedures, but do not compute final target candidates or answer letters.
