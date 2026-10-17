#!/usr/bin/env python3
"""把绕口令写进词书（demo/books/*.json）当例句。在 import_legacy.py / import_textbooks.py 之后跑。

绕口令来源：data/twister-samples.json（20 个样张）和 data/twisters/NNN.json（每批 20 条）。
Kron 2026-10-17：图用老版的，例句换成绕口令。所以每个词只换 s=绕口令、sc=中文；
img 不动，hint（脑洞）保留老版的（多半是在讲老图），老版没有脑洞的词才补上绕口令的。
同一个词在哪本书里都换成同一条（按 slug 认词：have / have. 共用一条）。

  python3 scripts/apply_twisters.py
"""
import glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

tw = {}
for f in [os.path.join(ROOT, 'data', 'twister-samples.json')] + sorted(glob.glob(os.path.join(ROOT, 'data', 'twisters', '[0-9]*.json'))):
    for it in json.load(open(f, encoding='utf-8')):
        tw.setdefault(slug(it['w']), it)

n = miss = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'demo', 'books', '*.json'))):
    b = json.load(open(f, encoding='utf-8'))
    for u in b['units']:
        for w in u['w']:
            it = tw.get(slug(w['w']))
            if not it: miss += 1; continue
            w['s'], w['sc'] = it['tw'], it['twc']
            if not w.get('hint'): w['hint'] = it['hint']
            n += 1
    with open(f, 'w', encoding='utf-8') as fp: json.dump(b, fp, ensure_ascii=False, separators=(',', ':'))
print(f'{len(tw)} 条绕口令，词书里换了 {n} 处，{miss} 处没有绕口令')
