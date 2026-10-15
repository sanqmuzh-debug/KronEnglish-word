#!/usr/bin/env python3
"""Build demo/data.js for the Kron Word redesign demo.

Reads every book in data/, splits each word into syllable blocks
(curated boxes when they already form real syllables, a heuristic
syllabifier otherwise), merges the hand-written tongue twisters from
demo/twisters.json and writes one compact `window.KRON_DATA` bundle.
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DEMO = os.path.join(ROOT, "demo")

BOOKS = [
    ("th0", "th0-vocab.json", "Think", "Starter", "#58CC02"),
    ("th1", "th1-vocab.json", "Think", "Level 1", "#1CB0F6"),
    ("th2", "th2-vocab.json", "Think", "Level 2", "#CE82FF"),
    ("th3", "think-l3-vocab.json", "Think", "Level 3", "#FF9600"),
    ("th4", "th4-vocab.json", "Think", "Level 4", "#FF4B4B"),
    ("th5", "th5-vocab.json", "Think", "Level 5", "#2B70C9"),
    ("pu0", "pu0-vocab.json", "Power Up", "Start Smart", "#FFC800"),
    ("pu1", "pu1-vocab.json", "Power Up", "Level 1", "#00CD9C"),
    ("pu2", "pu2-vocab.json", "Power Up", "Level 2", "#FF86D0"),
    ("pu3", "pu3-vocab.json", "Power Up", "Level 3", "#8E5CF7"),
    ("pu4", "pu4-vocab.json", "Power Up", "Level 4", "#FF7A45"),
]

VOWELS = set("aeiouy")
DIGRAPHS = {"ch", "sh", "th", "ph", "wh", "ck", "ng", "gh", "qu", "gu"}
BLENDS = {"bl", "br", "cl", "cr", "dr", "fl", "fr", "gl", "gr", "pl", "pr",
          "sc", "sk", "sl", "sm", "sn", "sp", "st", "sw", "tr", "tw", "wr", "kn"}
KEEP_TOGETHER = ("tion", "sion", "cian", "cious", "tious", "tial", "cial", "geous", "ture")


def is_vowel(word, i):
    c = word[i]
    if c in "aeiou":
        # 'u' right after q / g before another vowel is part of the consonant
        if c == "u" and i > 0 and word[i - 1] in "qg" and i + 1 < len(word) and word[i + 1] in "aeiouy":
            return False
        return True
    if c == "y":
        return i > 0 and word[i - 1] not in "aeiou"
    return False


def split_cluster(cl):
    """How many consonants of a cluster between two vowels stay with the left syllable."""
    n = len(cl)
    if n == 0:
        return 0
    if n == 1:
        return 1 if cl == "x" else 0
    if n == 2:
        if cl in ("ck", "gh"):
            return 2
        if cl in DIGRAPHS or cl in BLENDS - {"st", "sk", "sp", "sc", "sm", "sn", "sl", "sw"}:
            return 0
        return 1
    if cl[-3:] in ("str", "spr", "scr", "spl", "thr", "chr"):
        return n - 3
    if cl[-2:] in DIGRAPHS or cl[-2:] in BLENDS:
        return n - 2
    return n - 1


def syllabify(word):
    w = word.lower()
    if len(w) <= 2:
        return [word]
    groups = []  # (start, end) of vowel groups
    i = 0
    while i < len(w):
        if is_vowel(w, i):
            j = i
            while j + 1 < len(w) and is_vowel(w, j + 1):
                j += 1
            groups.append([i, j + 1])
            i = j + 1
        else:
            i += 1
    if not groups:
        return [word]
    # silent final e / -es / -ed belongs to the previous syllable
    last = groups[-1]
    if len(groups) > 1:
        tail = w[last[0]:]
        if (w.endswith("e") and last == [len(w) - 1, len(w)] and not w.endswith("le")) \
                or (tail in ("es", "ed") and w[last[0] - 1] not in "td" and not w.endswith("ses")):
            groups.pop()
    # consonant + le is its own syllable
    if len(w) > 3 and w.endswith("le") and not is_vowel(w, len(w) - 3) and len(groups) >= 2:
        pass  # handled naturally: 'e' is a vowel group, cluster split puts consonant before it
    cuts = []
    for a, b in zip(groups, groups[1:]):
        cl = w[a[1]:b[0]]
        k = split_cluster(cl)
        cuts.append(a[1] + k)
    # vowel pairs that are usually two syllables (li-on, cre-ate)
    out, prev = [], 0
    for c in cuts:
        out.append(word[prev:c])
        prev = c
    out.append(word[prev:])
    fixed = []
    for s in out:
        sl = s.lower()
        m = re.search(r"(ia|io|eo|ea|iu|ua|uo)", sl)
        if m and len(s) > 2 and not any(k in sl for k in KEEP_TOGETHER) and m.group(1) in ("ia", "io", "eo", "iu", "uo") \
                and not (m.start() > 0 and sl[m.start() - 1] in "qg"):
            fixed += [s[:m.start() + 1], s[m.start() + 1:]]
        else:
            fixed.append(s)
    out = [s for s in fixed if s]
    # glue pieces without a vowel back on
    merged = []
    for s in out:
        if merged and not any(ch in VOWELS for ch in s.lower()):
            merged[-1] += s
        else:
            merged.append(s)
    if merged and not any(ch in VOWELS for ch in merged[0].lower()) and len(merged) > 1:
        merged[1] = merged[0] + merged[1]
        merged.pop(0)
    return merged


def onset_rime(word):
    w = word.lower()
    i = 0
    while i < len(w) and not is_vowel(w, i) and not (w[i] == "y" and i > 0):
        i += 1
    if w.startswith("qu"):
        i = 2
    if 0 < i < len(w):
        return [word[:i], word[i:]]
    if i == 0:  # vowel-initial: vowel group + coda (e|gg, a|nt)
        j = 0
        while j < len(w) and is_vowel(w, j):
            j += 1
        if 0 < j < len(w) and len(w) > 2:
            return [word[:j], word[j:]]
    return [word]


def has_vowel(s):
    return any(c in VOWELS for c in s.lower())


def puzzle_text(text):
    t = re.sub(r"\([^)]*\)", " ", text)
    alts = [a.strip() for a in t.split("/")]
    alts = [a for a in alts if re.search(r"[A-Za-z]", a)]
    if not alts:
        return None
    t = alts[0]
    t = re.sub(r"[.,?!…:;]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t or None


def split_word(token, curated, alone):
    if curated and len(curated) >= 2 and all(has_vowel(c) for c in curated):
        return curated
    syl = syllabify(token)
    if len(syl) == 1 and (len(token) >= 4 or (alone and len(token) > 2)):
        syl = onset_rime(token)
    return syl


def encode(text, boxes):
    """Encode as 'pl|ay an in|stru|ment': '|' marks a block cut inside a letter run."""
    box_texts = [re.sub(r"[^A-Za-z]", "", b.get("text", "")) for b in boxes]
    box_texts = [b for b in box_texts if b]
    out = []
    bi = 0
    alone = len(re.findall(r"[A-Za-z]+", text)) == 1
    for run in re.split(r"([A-Za-z]+)", text):
        if not run:
            continue
        if not run.isalpha():
            out.append(run)
            continue
        curated = None
        # find consecutive boxes that spell exactly this run
        for start in range(bi, len(box_texts)):
            acc, k = "", start
            while k < len(box_texts) and len(acc) < len(run):
                acc += box_texts[k]
                k += 1
            if acc.lower() == run.lower():
                curated = []
                pos = 0
                for b in box_texts[start:k]:
                    curated.append(run[pos:pos + len(b)])
                    pos += len(b)
                bi = k
                break
        out.append("|".join(split_word(run, curated, alone)))
    return "".join(out)


def transfers(w):
    res = []
    for t in w.get("transfers") or []:
        if isinstance(t, dict) and t.get("word") and t.get("hl"):
            res.append([t["word"], t["hl"], t.get("cn", "")])
    return res[:4]


def main():
    twisters = json.load(open(os.path.join(DEMO, "twisters.json"), encoding="utf-8"))
    books = []
    total = 0
    for bid, fname, series, level, color in BOOKS:
        d = json.load(open(os.path.join(DATA, fname), encoding="utf-8"))
        seen, units = set(), []
        for key, u in d.items():
            if not isinstance(u, dict) or not isinstance(u.get("words"), list) or not u["words"]:
                continue
            ids = tuple(w.get("id") for w in u["words"])
            if ids in seen:
                continue
            seen.add(ids)
            words = []
            for w in u["words"]:
                pt = puzzle_text(w.get("text", ""))
                if not pt:
                    continue
                item = {
                    "t": w["text"],
                    "b": encode(pt, w.get("boxes") or []),
                    "i": w.get("ipa", ""),
                    "m": w.get("translation") or w.get("definition", ""),
                    "k": w.get("kronTip", ""),
                }
                if w.get("example"):
                    item["e"] = w["example"]
                if w.get("exampleTranslation"):
                    item["ec"] = w["exampleTranslation"]
                x = transfers(w)
                if x:
                    item["x"] = x
                tw = twisters.get(pt.lower())
                if tw:
                    item.update({"tw": tw["en"], "twc": tw["cn"], "sc": tw["scene"], "em": tw["emoji"]})
                words.append(item)
            if words:
                units.append({"n": u.get("unitName") or key, "t": u.get("title", ""), "w": words})
                total += len(words)
        books.append({"id": bid, "series": series, "level": level, "color": color, "units": units})
    featured = []
    for b in books:
        for ui, u in enumerate(b["units"]):
            n = sum(1 for w in u["w"] if "tw" in w)
            if n >= 6:
                featured.append({"book": b["id"], "unit": ui})
    payload = {"books": books, "featured": featured}
    js = "window.KRON_DATA=" + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    with open(os.path.join(DEMO, "data.js"), "w", encoding="utf-8") as f:
        f.write(js)
    print(f"books={len(books)} words={total} featured={featured} size={len(js.encode())/1024:.0f}KB")


if __name__ == "__main__":
    main()
