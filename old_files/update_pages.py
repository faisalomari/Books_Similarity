# -*- coding: utf-8 -*-
import os, re, csv, glob
from typing import List, Dict, Tuple, Optional
from tqdm import tqdm

# ---------------------------
# Arabic normalization (same spirit as your code)
# ---------------------------
ARABIC_DIAC = r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]"
PUNCT = r"[^\w\s\u0600-\u06FF]"  # keep Arabic letters/digits/underscore/space

def normalize_ar(text: str) -> str:
    if not text:
        return ""
    t = re.sub(ARABIC_DIAC, "", text)
    t = t.replace("ـ", "")  # tatweel
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ى", "ي")
    t = t.replace("ة", "ه")
    t = re.sub(PUNCT, " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

# ---------------------------
# Load per-page TXT files
# Expect files like: book_page_1.txt, book_page_2.txt, ...
# ---------------------------
def load_pages(dir_path: str, pattern: str = "book_page_*.txt") -> List[Dict]:
    """
    Returns a list of dicts:
      { "page": int, "raw": str, "norm": str, "path": str }
    Pages are sorted by page number.
    """
    files = sorted(glob.glob(os.path.join(dir_path, pattern)),
                   key=lambda p: int(re.search(r"book_page_(\d+)\.txt", os.path.basename(p)).group(1)))
    pages = []
    for fp in tqdm(files, desc=f"Loading pages from {dir_path}"):
        m = re.search(r"book_page_(\d+)\.txt", os.path.basename(fp))
        if not m:
            # skip files that don't match the pattern
            continue
        page_no = int(m.group(1))
        with open(fp, "r", encoding="utf-8") as f:
            raw = f.read()
        pages.append({
            "page": page_no,
            "raw": raw,
            "norm": normalize_ar(raw),
            "path": fp
        })
    return pages

# ---------------------------
# Find page for a sentence
# 1) exact substring search on normalized text
# 2) optional fuzzy fallback (off by default to avoid false positives)
# ---------------------------
def find_page_for_sentence(sentence: str,
                           pages: List[Dict],
                           use_fuzzy: bool = False,
                           fuzzy_cutoff: int = 92) -> Optional[int]:
    s_norm = normalize_ar(sentence)
    if not s_norm:
        return None

    # Exact normalized substring search
    for p in pages:
        if s_norm in p["norm"]:
            return p["page"]

    if not use_fuzzy:
        return None

    # Optional fuzzy fallback (very conservative)
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return None

    best_page, best_score = None, -1
    # To keep it fast, look for long substrings of s_norm as anchors
    anchor = s_norm if len(s_norm) <= 80 else s_norm[:80]
    for p in pages:
        # quick filter: the anchor must appear at least partially
        # If not, compute a quick ratio on the whole page (expensive!)
        score = fuzz.partial_ratio(s_norm, p["norm"])
        if score > best_score:
            best_score, best_page = score, p["page"]

    return best_page if best_score >= fuzzy_cutoff else None

# ---------------------------
# Update CSV positions based on TXT pages
# ---------------------------
def update_csv_pages(csv_in: str,
                     csv_out: str,
                     ihya_pages_dir: str,
                     qut_pages_dir: str,
                     ihya_use_fuzzy: bool = False,
                     qut_use_fuzzy: bool = False):
    # Load pages
    ihya_pages = load_pages(ihya_pages_dir)
    qut_pages  = load_pages(qut_pages_dir)

    rows_in: List[Dict] = []
    with open(csv_in, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            raise RuntimeError("CSV has no header.")
        rows_in = list(reader)

    # Ensure required columns exist
    required = {"pos_in_ihya", "pos_in_qut", "sentence_ihya", "sentence_qut"}
    missing = required - set(fieldnames)
    if missing:
        raise RuntimeError(f"CSV missing required columns: {missing}")

    # Process rows
    rows_out: List[Dict] = []
    for r in tqdm(rows_in, desc="Updating pages"):
        pos_ihya_old = r.get("pos_in_ihya", "")
        pos_qut_old  = r.get("pos_in_qut", "")
        s_ihya       = r.get("sentence_ihya", "") or ""
        s_qut        = r.get("sentence_qut", "") or ""

        # Find pages
        ihya_page = find_page_for_sentence(s_ihya, ihya_pages, use_fuzzy=ihya_use_fuzzy)
        qut_page  = find_page_for_sentence(s_qut,  qut_pages,  use_fuzzy=qut_use_fuzzy)

        # Update if found, else keep old
        if ihya_page is not None:
            r["pos_in_ihya"] = f"{ihya_page}"
        else:
            # keep original if present
            r["pos_in_ihya"] = pos_ihya_old or ""

        if qut_page is not None:
            r["pos_in_qut"] = f"{qut_page}"
        else:
            r["pos_in_qut"] = pos_qut_old or ""

        rows_out.append(r)

    # Write updated CSV
    with open(csv_out, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"Done. Wrote updated CSV -> {csv_out}")

# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    # Folders containing per-page text files:
    #   ihya_pages/book_page_1.txt, book_page_2.txt, ...
    #   qut_pages/book_page_1.txt,  book_page_2.txt, ...
    IHYA_DIR = "algazaly/book"
    QUT_DIR  = "almaky/book"

    CSV_IN  = "quotes_ihya_from_qut_scored_sequential.csv"
    CSV_OUT = "quotes_ihya_from_qut_scored_with_pages.csv"

    update_csv_pages(CSV_IN, CSV_OUT, IHYA_DIR, QUT_DIR,
                     ihya_use_fuzzy=False,   # set True if you need a cautious fuzzy fallback
                     qut_use_fuzzy=False)
