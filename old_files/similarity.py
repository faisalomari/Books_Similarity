# -*- coding: utf-8 -*-
import os, re, csv, difflib
from typing import List, Dict, Tuple
from docx import Document
from docx.oxml.ns import qn
from rapidfuzz import process, fuzz
from tqdm import tqdm

# ---------------------------
# Arabic normalization
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
# DOCX sentence extraction
# ---------------------------
SENT_SPLIT = re.compile(r"[\.!\?؟…]+|\n+")

def iter_docx_sentences(docx_path: str) -> List[Dict]:
    """
    Returns list of dicts:
      { "raw": str, "norm": str, "pos": "page:X" or "p:idx" }
    """
    doc = Document(docx_path)
    page_no = 1
    results = []
    para_idx = 0

    for para in tqdm(doc.paragraphs, desc=f"Extracting from {os.path.basename(docx_path)}"):
        for run in para.runs:
            for child in run._r:
                if child.tag == qn('w:br') and child.get(qn('w:type')) == 'page':
                    page_no += 1

        raw_para = para.text.strip()
        if not raw_para:
            para_idx += 1
            continue

        parts = [s.strip() for s in SENT_SPLIT.split(raw_para) if s.strip()]
        for s in parts:
            if len(s) < 12:
                continue
            results.append({
                "raw": s,
                "norm": normalize_ar(s),
                "pos": f"page:{page_no}" if page_no >= 1 else f"p:{para_idx}"
            })
        para_idx += 1
    return results

# ---------------------------
# Utility: overlap estimator (chars)
# ---------------------------
def overlap_chars(a: str, b: str) -> int:
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return sum(block.size for block in sm.get_matching_blocks())

# ---------------------------
# Sequential matching
# ---------------------------
def match_books_sequential(book1_docx: str,
                           book2_docx: str,
                           out_csv: str,
                           min_len_chars: int = 24,
                           score_threshold: int = 70):
    # 1) Extract sentences
    book1_sents = iter_docx_sentences(book1_docx)
    book2_sents = iter_docx_sentences(book2_docx)
    book2_norms = [s["norm"] for s in book2_sents]

    rows: List[Tuple[str, str, str, str, int, int]] = []

    # 2) Match sequentially
    for s1 in tqdm(book1_sents, desc="Matching sequentially"):
        if len(s1["raw"]) < min_len_chars:
            continue
        if len(s1["norm"].split()) < 4:
            continue

        m = process.extractOne(
            s1["norm"],
            book2_norms,
            scorer=fuzz.token_set_ratio,
            score_cutoff=score_threshold
        )
        if not m:
            continue

        _, score, idx2 = m
        strict_score = fuzz.QRatio(s1["norm"], book2_sents[idx2]["norm"])
        if strict_score < score_threshold - 5:
            continue

        pos1 = s1["pos"]
        pos2 = book2_sents[idx2]["pos"]
        raw1 = s1["raw"]
        raw2 = book2_sents[idx2]["raw"]
        ov   = overlap_chars(s1["norm"], book2_sents[idx2]["norm"])
        rows.append((pos1, pos2, raw1, raw2, int(score), ov))

    # 3) Sort results
    rows.sort(key=lambda r: (r[4], r[5]), reverse=True)

    # 4) Write CSV
    os.makedirs(os.path.dirname(out_csv) or ".", exist_ok=True)
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "pos_in_ihya",
            "pos_in_qut",
            "sentence_ihya",
            "sentence_qut",
            "score",
            "overlap_chars"
        ])
        w.writerows(rows)

    print(f"Done. Matches written: {len(rows)} rows -> {out_csv}")

# ---------------------------
# CLI
# ---------------------------
if __name__ == "__main__":
    ihya_docx = "algazaly/combined_book.docx"   # احياء علوم الدين
    qut_docx  = "almaky/combined_book.docx"     # قوت القلوب

    out_csv = "quotes_ihya_from_qut_scored_sequential.csv"
    match_books_sequential(
        ihya_docx,
        qut_docx,
        out_csv,
        min_len_chars=24,
        score_threshold=60
    )
