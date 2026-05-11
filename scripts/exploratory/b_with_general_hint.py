from mlx_lm import load, generate

MODEL_ID = "Qwen/Qwen3.5-4B"

model, tokenizer = load(MODEL_ID)

messages = [
    {"role": "user", "content": """"
    You are solving a multiple-choice logic question.

Exactly six trade representatives negotiate a treaty: Klosnik, Londi, Manley, Neri, Osata, Poirier. There are exactly six chairs evenly spaced around a circular table. The chairs are numbered 1 through 6, with successively numbered chairs next to each other and chair 1 next to chair 6. Each chair is occupied by exactly one of the representatives.

Rules:
1. Poirier sits immediately next to Neri.
2. Londi sits immediately next to Manley, Neri, or both.
3. Klosnik does not sit immediately next to Manley.
4. If Osata sits immediately next to Poirier, then Osata does not sit immediately next to Manley.

Question:
If Klosnik sits directly between Londi and Poirier, then Manley must sit directly between

A. Londi and Neri
B. Londi and Osata
C. Neri and Osata
D. Neri and Poirier
E. Osata and Poirier

Hint:
Use forced local structure rather than full enumeration. First lock in all required adjacency relations. “Klosnik sits directly between Londi and Poirier” means Klosnik is adjacent to both Londi and Poirier, so Londi–Klosnik–Poirier or its mirror forms a fixed three-person segment. Since Poirier must also be adjacent to Neri, Poirier’s other open side is forced to Neri. Now apply Londi’s rule carefully: Londi must be adjacent to Manley, Neri, or both, but Londi is already adjacent to Klosnik on one side, so its only remaining open neighbor must supply that requirement. Use that forced placement first, then place the two remaining people in the only remaining seats and check which “between” relationship for Manley is unavoidable. Prefer forced-neighbor reasoning, open-slot counting, and block extension over case-by-case search.

Return exactly one capital letter: A, B, C, D, or E.
    """}
]

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    enable_thinking=False,
)

text = generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=16384,
    verbose=False,
)

print(text)
# C