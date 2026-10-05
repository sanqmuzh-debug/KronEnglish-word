#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit all 125 Kron Word HTML modules in public/word/
Checks:
1. Total Phonics & Morpheme Chunking (0 uncut words > 2 letters).
2. Transfer Homomorphism (0 hl mismatches).
3. Aha! Notebook Sync Logic.
"""

import os
import re
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD_DIR = os.path.join(BASE_DIR, "public", "word")

files = sorted([f for f in os.listdir(WORD_DIR) if f.endswith(".html")])

uncut_words = []
transfer_mismatches = []
missing_sync = []
total_words = 0

for f in files:
    path = os.path.join(WORD_DIR, f)
    with open(path, "r", encoding="utf-8") as fp:
        c = fp.read()

    if "id=\"ahaSyncBanner\"" not in c or "function syncFromAha()" not in c:
        missing_sync.append(f)

    m = re.search(r'const VOCABULARY = (\[.*?\]);', c, re.DOTALL)
    if not m:
        print(f"Error: No VOCABULARY found in {f}")
        continue

    try:
        voc = json.loads(m.group(1))
    except Exception as e:
        print(f"JSON error in {f}: {e}")
        continue

    for item in voc:
        total_words += 1
        blocks = item.get("blocks", [])
        word = item.get("word", "")

        if len(blocks) == 1 and len(blocks[0]) > 2:
            uncut_words.append((f, word, blocks[0]))

        for t in item.get("transfers", []):
            hl = t.get("hl", "")
            if hl and hl not in blocks:
                transfer_mismatches.append((f, word, hl, blocks))

print("==========================================")
print("📊 KronEnglish-word Quality Audit Report")
print("==========================================")
print(f"📁 Total HTML files audited: {len(files)}")
print(f"📖 Total vocabulary items:   {total_words}")
print(f"🧩 Uncut words (> 2 chars):  {len(uncut_words)}")
if uncut_words:
    print(f"   Examples: {uncut_words[:10]}")
print(f"🎯 Transfer hl mismatches:   {len(transfer_mismatches)}")
if transfer_mismatches:
    print(f"   Examples: {transfer_mismatches[:10]}")
print(f"⚡ Missing Aha! sync:        {len(missing_sync)}")
if missing_sync:
    print(f"   Examples: {missing_sync[:10]}")
print("==========================================")
if len(uncut_words) == 0 and len(transfer_mismatches) == 0 and len(missing_sync) == 0:
    print("🌟 100% GOLD STANDARD COMPLIANCE ACHIEVED!")
