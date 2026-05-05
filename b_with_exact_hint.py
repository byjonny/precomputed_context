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
Use forced-block reasoning and track open neighbor slots exactly. “Klosnik sits directly between Londi and Poirier” fixes the local block Londi–Klosnik–Poirier or its mirror, so Klosnik is adjacent to both Londi and Poirier. Since Poirier must also be adjacent to Neri and already uses one side for Klosnik, Poirier’s only other neighbor is forced to be Neri. This gives a four-person block Londi–Klosnik–Poirier–Neri or its mirror. Now inspect Londi: one of Londi’s neighbors is already Klosnik, and in this forced four-person block Londi is not adjacent to Neri. Therefore Londi cannot satisfy its rule through Neri here, so Londi’s only remaining open neighbor must be Manley. That extends the block to Manley–Londi–Klosnik–Poirier–Neri or its mirror. The only remaining person, Osata, fills the last seat, so Manley’s two neighbors must be Londi and Osata. Do not enumerate cases; extend the forced block step by step from exhausted neighbor slots.

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

# B