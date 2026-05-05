# Structured Transfer Eval

- Run id: `positive50_structured_v1`
- Model: `Qwen/Qwen3.5-4B`
- Thinking mode: `enable_thinking=False`
- Levels: `none, structured`
- Eval offset: `20`
- Limit per dataset: `50`

| Dataset | Source | None | Structured | Delta | None-wrong recovered | None-correct harmed |
|---|---|---:|---:|---:|---:|---:|
| `bbh_date` | lukaemon/bbh:date_understanding | 32/50 (64.0%) | 38/50 (76.0%) | +6 | 7/18 | 1/32 |
| `bbh_formal_fallacies` | lukaemon/bbh:formal_fallacies | 28/50 (56.0%) | 31/50 (62.0%) | +3 | 7/22 | 4/28 |
| `prontoqa` | renma/ProntoQA:dev_gpt4 | 35/50 (70.0%) | 39/50 (78.0%) | +4 | 4/15 | 0/35 |
| `proofwriter` | tasksource/proofwriter:validation | 29/50 (58.0%) | 31/50 (62.0%) | +2 | 5/21 | 3/29 |
| `reclor` | hadithya369/ReClor:validation | 37/50 (74.0%) | 36/50 (72.0%) | -1 | 3/13 | 4/37 |
| `winogrande` | allenai/winogrande:winogrande_debiased/validation | 37/50 (74.0%) | 38/50 (76.0%) | +1 | 3/13 | 2/37 |

## Dataset Notes

### `bbh_date`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: First few date-understanding examples: identify anchor date, requested offset, and output format.
- Recovered rows: 21, 25, 33, 35, 36, 45, 50
- Harmed rows: 66

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | B | B |
| 21 | B | A | B |
| 22 | D | A | A |
| 23 | C | B | D |
| 24 | A | A | A |
| 25 | D | A | D |
| 26 | F | F | F |
| 27 | B | A | E |
| 28 | F | B | B |
| 29 | D | D | D |
| 30 | E | E | E |
| 31 | C | A | A |
| 32 | B | C | C |
| 33 | F | B | F |
| 34 | D | D | D |
| 35 | D | A | D |
| 36 | B | A | B |
| 37 | B | B | B |
| 38 | B | B | B |
| 39 | A | A | A |
| 40 | B | B | B |
| 41 | E | B | B |
| 42 | E | E | E |
| 43 | A | B | B |
| 44 | D | D | D |
| 45 | F | A | F |
| 46 | C | C | C |
| 47 | E | E | E |
| 48 | F | F | F |
| 49 | B | A | D |
| 50 | E | B | E |
| 51 | D | D | D |
| 52 | D | D | D |
| 53 | B | B | B |
| 54 | A | A | A |
| 55 | C | D | D |
| 56 | A | A | A |
| 57 | A | A | A |
| 58 | F | F | F |
| 59 | D | D | D |
| 60 | E | E | E |
| 61 | B | B | B |
| 62 | D | D | D |
| 63 | E | C | C |
| 64 | D | D | D |
| 65 | B | B | B |
| 66 | A | A | E |
| 67 | C | C | C |
| 68 | E | E | E |
| 69 | F | F | F |

### `bbh_formal_fallacies`

- Dataset URL: https://huggingface.co/datasets/lukaemon/bbh
- Template seed: First few formal-fallacy examples: separate premises from conclusion and check entailment direction.
- Recovered rows: 20, 36, 49, 50, 60, 63, 64
- Harmed rows: 38, 43, 45, 69

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | A | B |
| 21 | B | A | A |
| 22 | A | A | A |
| 23 | A | A | A |
| 24 | B | A | A |
| 25 | A | A | A |
| 26 | A | A | A |
| 27 | B | B | B |
| 28 | A | B | B |
| 29 | B | A | A |
| 30 | B | A | A |
| 31 | A | A | A |
| 32 | B | A | A |
| 33 | A | A | A |
| 34 | A | A | A |
| 35 | A | A | A |
| 36 | B | A | B |
| 37 | B | A | A |
| 38 | B | B | A |
| 39 | B | A | A |
| 40 | B | A | A |
| 41 | A | A | A |
| 42 | B | B | B |
| 43 | A | A | B |
| 44 | A | A | A |
| 45 | A | A | B |
| 46 | B | A | A |
| 47 | A | A | A |
| 48 | A | A | A |
| 49 | B | A | B |
| 50 | B | A | B |
| 51 | B | A | A |
| 52 | A | A | A |
| 53 | A | A | A |
| 54 | B | A | A |
| 55 | A | A | A |
| 56 | B | B | B |
| 57 | A | A | A |
| 58 | B | A | A |
| 59 | A | A | A |
| 60 | B | A | B |
| 61 | A | A | A |
| 62 | A | A | A |
| 63 | B | A | B |
| 64 | B | A | B |
| 65 | B | A | A |
| 66 | A | A | A |
| 67 | A | A | A |
| 68 | B | A | A |
| 69 | A | A | B |

### `prontoqa`

- Dataset URL: https://huggingface.co/datasets/renma/ProntoQA
- Template seed: Earlier ProntoQA hint-lab cases: forward-chain from subject facts to query predicate.
- Recovered rows: ProntoQA_28, ProntoQA_40, ProntoQA_45, ProntoQA_67
- Harmed rows: -

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| ProntoQA_21 | A | A | A |
| ProntoQA_22 | B | A | A |
| ProntoQA_23 | A | A | A |
| ProntoQA_24 | A | A | A |
| ProntoQA_25 | A | A | A |
| ProntoQA_26 | A | A | A |
| ProntoQA_27 | A | A | A |
| ProntoQA_28 | B | A | B |
| ProntoQA_29 | B | B | B |
| ProntoQA_30 | A | A | A |
| ProntoQA_31 | A | A | A |
| ProntoQA_32 | A | A | A |
| ProntoQA_33 | B | A | A |
| ProntoQA_34 | B | B | B |
| ProntoQA_35 | A | A | A |
| ProntoQA_36 | A | A | A |
| ProntoQA_37 | A | A | A |
| ProntoQA_38 | A | A | A |
| ProntoQA_39 | B | A | A |
| ProntoQA_40 | A | B | A |
| ProntoQA_41 | A | A | A |
| ProntoQA_42 | B | A | A |
| ProntoQA_43 | A | A | A |
| ProntoQA_44 | B | A | A |
| ProntoQA_45 | A | B | A |
| ProntoQA_46 | A | A | A |
| ProntoQA_47 | B | A | A |
| ProntoQA_48 | A | A | A |
| ProntoQA_49 | B | B | B |
| ProntoQA_50 | B | A | A |
| ProntoQA_51 | B | A | A |
| ProntoQA_52 | A | A | A |
| ProntoQA_53 | A | A | A |
| ProntoQA_54 | A | A | A |
| ProntoQA_55 | A | A | A |
| ProntoQA_56 | A | A | A |
| ProntoQA_57 | A | A | A |
| ProntoQA_58 | B | A | A |
| ProntoQA_59 | A | A | A |
| ProntoQA_60 | B | B | B |
| ProntoQA_61 | A | A | A |
| ProntoQA_62 | A | A | A |
| ProntoQA_63 | A | A | A |
| ProntoQA_64 | A | A | A |
| ProntoQA_65 | B | B | B |
| ProntoQA_66 | B | A | A |
| ProntoQA_67 | A | B | A |
| ProntoQA_68 | A | A | A |
| ProntoQA_69 | A | A | A |
| ProntoQA_70 | B | A | A |

### `proofwriter`

- Dataset URL: https://huggingface.co/datasets/tasksource/proofwriter
- Template seed: First few ProofWriter examples: forward-chain from facts and rules to the queried statement.
- Recovered rows: 23:RelNoneg-OWA-D0-5791, 41:AttNeg-OWA-D0-1627, 46:AttNeg-OWA-D0-4365, 49:RelNoneg-OWA-D0-6247, 58:RelNeg-OWA-D0-1507
- Harmed rows: 35:AttNoneg-OWA-D0-6891, 57:RelNeg-OWA-D0-1507, 61:RelNeg-OWA-D0-4996

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20:RelNoneg-OWA-D0-5791 | A | A | A |
| 21:RelNoneg-OWA-D0-5791 | B | A | A |
| 22:RelNoneg-OWA-D0-5791 | C | C | C |
| 23:RelNoneg-OWA-D0-5791 | C | B | C |
| 24:AttNeg-OWA-D0-5908 | A | A | A |
| 25:AttNeg-OWA-D0-5908 | B | C | A |
| 26:AttNeg-OWA-D0-5908 | C | C | C |
| 27:AttNeg-OWA-D0-5908 | C | C | C |
| 28:AttNeg-OWA-D0-2030 | A | A | A |
| 29:AttNeg-OWA-D0-2030 | B | B | B |
| 30:AttNeg-OWA-D0-2030 | C | A | A |
| 31:AttNeg-OWA-D0-2030 | C | B | B |
| 32:AttNoneg-OWA-D0-6891 | A | A | A |
| 33:AttNoneg-OWA-D0-6891 | B | B | B |
| 34:AttNoneg-OWA-D0-6891 | C | A | A |
| 35:AttNoneg-OWA-D0-6891 | C | C | B |
| 36:AttNoneg-OWA-D0-6318 | A | A | A |
| 37:AttNoneg-OWA-D0-6318 | B | B | B |
| 38:AttNoneg-OWA-D0-6318 | C | A | A |
| 39:AttNoneg-OWA-D0-6318 | C | B | A |
| 40:AttNeg-OWA-D0-1627 | A | A | A |
| 41:AttNeg-OWA-D0-1627 | B | C | B |
| 42:AttNeg-OWA-D0-1627 | C | C | C |
| 43:AttNeg-OWA-D0-1627 | C | B | B |
| 44:AttNeg-OWA-D0-4365 | A | A | A |
| 45:AttNeg-OWA-D0-4365 | B | B | B |
| 46:AttNeg-OWA-D0-4365 | C | A | C |
| 47:AttNeg-OWA-D0-4365 | C | C | C |
| 48:RelNoneg-OWA-D0-6247 | A | A | A |
| 49:RelNoneg-OWA-D0-6247 | B | A | B |
| 50:RelNoneg-OWA-D0-6247 | C | A | A |
| 51:RelNoneg-OWA-D0-6247 | C | B | B |
| 52:AttNeg-OWA-D0-1163 | A | A | A |
| 53:AttNeg-OWA-D0-1163 | B | B | B |
| 54:AttNeg-OWA-D0-1163 | C | A | A |
| 55:AttNeg-OWA-D0-1163 | C | B | B |
| 56:RelNeg-OWA-D0-1507 | A | A | A |
| 57:RelNeg-OWA-D0-1507 | B | B | A |
| 58:RelNeg-OWA-D0-1507 | C | A | C |
| 59:RelNeg-OWA-D0-1507 | C | C | C |
| 60:RelNeg-OWA-D0-4996 | A | A | A |
| 61:RelNeg-OWA-D0-4996 | B | B | A |
| 62:RelNeg-OWA-D0-4996 | C | A | B |
| 63:RelNeg-OWA-D0-4996 | C | B | B |
| 64:AttNeg-OWA-D0-2646 | A | A | A |
| 65:AttNeg-OWA-D0-2646 | B | C | A |
| 66:AttNeg-OWA-D0-2646 | C | C | C |
| 67:AttNeg-OWA-D0-2646 | C | C | C |
| 68:AttNoneg-OWA-D0-6191 | A | A | A |
| 69:AttNoneg-OWA-D0-6191 | B | A | A |

### `reclor`

- Dataset URL: https://huggingface.co/datasets/hadithya369/ReClor
- Template seed: First few ReClor logical-reading examples: separate argument, question task, and answer-choice roles.
- Recovered rows: val_28, val_30, val_57
- Harmed rows: val_25, val_39, val_47, val_55

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| val_20 | B | B | B |
| val_21 | D | A | A |
| val_22 | D | D | D |
| val_23 | B | B | B |
| val_24 | D | D | D |
| val_25 | D | D | C |
| val_26 | C | C | C |
| val_27 | C | C | C |
| val_28 | C | D | C |
| val_29 | B | D | D |
| val_30 | A | D | A |
| val_31 | B | B | B |
| val_32 | A | A | A |
| val_33 | D | B | B |
| val_34 | B | B | B |
| val_35 | C | D | D |
| val_36 | B | B | B |
| val_37 | D | C | C |
| val_38 | D | D | D |
| val_39 | D | D | A |
| val_40 | B | B | B |
| val_41 | A | A | A |
| val_42 | C | C | C |
| val_43 | B | C | C |
| val_44 | B | B | B |
| val_45 | A | A | A |
| val_46 | B | C | C |
| val_47 | A | A | C |
| val_48 | C | C | C |
| val_49 | D | D | D |
| val_50 | A | D | B |
| val_51 | D | A | A |
| val_52 | A | A | A |
| val_53 | C | C | C |
| val_54 | B | B | B |
| val_55 | A | A | C |
| val_56 | D | D | D |
| val_57 | B | A | B |
| val_58 | B | B | B |
| val_59 | C | C | C |
| val_60 | C | C | C |
| val_61 | D | D | D |
| val_62 | D | D | D |
| val_63 | B | D | C |
| val_64 | A | A | A |
| val_65 | B | B | B |
| val_66 | D | D | D |
| val_67 | C | C | C |
| val_68 | C | C | C |
| val_69 | A | A | A |

### `winogrande`

- Dataset URL: https://huggingface.co/datasets/allenai/winogrande
- Template seed: First few WinoGrande examples: compare candidate fillers by semantic role in the sentence.
- Recovered rows: 26, 60, 62
- Harmed rows: 45, 54

| Row | Gold | None | Structured |
|---:|---:|---:|---:|
| 20 | B | B | B |
| 21 | B | B | B |
| 22 | B | A | A |
| 23 | A | A | A |
| 24 | B | B | B |
| 25 | A | A | A |
| 26 | A | B | A |
| 27 | A | A | A |
| 28 | A | A | A |
| 29 | A | A | A |
| 30 | A | A | A |
| 31 | A | A | A |
| 32 | B | B | B |
| 33 | A | A | A |
| 34 | B | A | A |
| 35 | B | B | B |
| 36 | B | A | A |
| 37 | A | A | A |
| 38 | B | A | A |
| 39 | B | B | B |
| 40 | A | A | A |
| 41 | A | A | A |
| 42 | B | B | B |
| 43 | A | B | B |
| 44 | B | B | B |
| 45 | A | A | B |
| 46 | B | A | A |
| 47 | B | B | B |
| 48 | B | B | B |
| 49 | A | A | A |
| 50 | A | A | A |
| 51 | B | A | A |
| 52 | A | A | A |
| 53 | B | B | B |
| 54 | A | A | B |
| 55 | B | B | B |
| 56 | B | B | B |
| 57 | B | B | B |
| 58 | A | B | B |
| 59 | A | A | A |
| 60 | B | A | B |
| 61 | B | B | B |
| 62 | B | A | B |
| 63 | A | A | A |
| 64 | B | A | A |
| 65 | B | B | B |
| 66 | A | B | B |
| 67 | B | B | B |
| 68 | B | B | B |
| 69 | A | A | A |

## Guardrail

Structured hints are generated from question text only. They list task structure, entities, clue sentences, option maps, and reusable procedures, but do not compute final target candidates or answer letters.
