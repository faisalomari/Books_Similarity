import os
import re
import shutil

# ========= settings =========
SRC_DIR = r"output/book_11111/book"        # folder where original page_(num).txt are
DST_DIR = r"output/book_1111/book"      # new folder to put renamed files
# ============================

os.makedirs(DST_DIR, exist_ok=True)

pattern = re.compile(r"^page_(\d+)\.txt$", re.IGNORECASE)

for fname in os.listdir(SRC_DIR):
    match = pattern.match(fname)
    if match:
        num = match.group(1)  # extract the number
        new_name = f"book_page_{num}.txt"
        src_path = os.path.join(SRC_DIR, fname)
        dst_path = os.path.join(DST_DIR, new_name)

        shutil.copy2(src_path, dst_path)  # copy with metadata
        print(f"Copied: {fname} -> {new_name}")

print(f"\n✅ Done! Renamed files are in '{DST_DIR}'")
