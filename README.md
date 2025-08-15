# 📚 Shamela Books Similarity Tool

This project compares the text of **two books** from [Shamela.ws](https://shamela.ws) and finds **matching sentences** between them.  
It downloads the books page-by-page, cleans and normalizes the text, removes repeated formulas, converts to DOCX, matches using fuzzy similarity, and outputs CSV results with **page number mapping**.

## 🚀 Features
- **Threaded page extraction** for faster downloads from Shamela.
- **Arabic text normalization** (removes diacritics, unifies characters, cleans punctuation).
- **Stop phrases filtering** (e.g., _بسم الله الرحمن الرحيم_, _صلى الله عليه وسلم_, etc.).
- **DOCX generation** from per-page text.
- **Sentence extraction** with page tracking.
- **Fuzzy matching** with `RapidFuzz` for sentence similarity.
- **CSV output** of matches, with optional fuzzy page number mapping.

## 📦 Installation
```bash
pip install -r requirements.txt
```

## ⚙️ Usage
Edit `main.py` and set:
```python
book1_id = 8370  # First Shamela book ID
book2_id = 9472  # Second Shamela book ID
```
Run:
```bash
python main.py
```

## 📂 Pipeline Overview
1. Page Extraction
2. DOCX Building
3. Sentence Extraction & Filtering
4. Matching
5. Page Number Mapping

## 📤 Outputs
- `book_<ID>/book/` → per-page `.txt` files.
- `book_<ID>/combined_book.docx` → full book in DOCX.
- `matches_<ID1>_vs_<ID2>.csv` → matched sentences without page mapping.
- `matches_<ID1>_vs_<ID2>_with_pages.csv` → matched sentences **with** page mapping.

## 🛠 Requirements
See `requirements.txt`.

## ⚠️ Notes
- Excessive scraping might be blocked by Shamela.
- Adjust `max_workers` and `batch_size` if needed.
