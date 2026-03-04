# main.py
# -*- coding: utf-8 -*-
from shamela_tools import run_full_pipeline

# === Set your book IDs here ===
book1_id = 1111
book2_id = 9472

# === Settings ===
workdir = "output"
max_pages = 5000
stop_after_empty = 2
score_threshold = 70
min_len_chars = 24
use_fuzzy_backmap = False  # Set True if you want fuzzy mapping of page numbers

outputs = run_full_pipeline(
    book1_id=book1_id,
    book2_id=book2_id,
    workdir=workdir,
    max_pages=max_pages,
    stop_after_empty=stop_after_empty,
    score_threshold=score_threshold,
    min_len_chars=min_len_chars,
    use_fuzzy_backmap=use_fuzzy_backmap
)

print("\n=== Done ===")
for k, v in outputs.items():
    print(f"{k}: {v}")