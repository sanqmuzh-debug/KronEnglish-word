#!/usr/bin/env python3
"""把绕口令和新图写进词书（demo/books/*.json）。在 import_legacy.py / import_textbooks.py 之后跑。

绕口令来源：data/twister-samples.json（20 个样张）和 data/twisters/NNN.json（每批 20 条）。
图：data/tw-images.txt 里列着已经传进 R2（kronword-images）的 tw-<slug>.webp，图到了的词才整套换上。
同一个词在哪本书里都换成同一套：s=绕口令，sc=中文，hint=脑洞，img=tw-<slug>.webp。

  python3 scripts/apply_twisters.py
"""
import glob, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

tw = {}
for f in [os.path.join(ROOT, 'data', 'twister-samples.json')] + sorted(glob.glob(os.path.join(ROOT, 'data', 'twisters', '[0-9]*.json'))):
    for it in json.load(open(f, encoding='utf-8')):
        tw.setdefault(slug(it['w']), it)  # 按图名认词：have / have. 这类同名的共用一条、一张图
have = set(open(os.path.join(ROOT, 'data', 'tw-images.txt')).read().split()) if os.path.exists(os.path.join(ROOT, 'data', 'tw-images.txt')) else set()

n = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'demo', 'books', '*.json'))):
    b = json.load(open(f, encoding='utf-8')); hit = False
    for u in b['units']:
        for w in u['w']:
            it = tw.get(slug(w['w']))
            if not it or f"tw-{slug(it['w'])}.webp" not in have: continue  # 图到了才换，免得绕口令配着旧图
            w['s'], w['sc'], w['hint'], w['img'] = it['tw'], it['twc'], it['hint'], f"tw-{slug(it['w'])}.webp"
            hit = True; n += 1
    if hit:
        with open(f, 'w', encoding='utf-8') as fp: json.dump(b, fp, ensure_ascii=False, separators=(',', ':'))
print(f'{len(tw)} 条绕口令，词书里换了 {n} 处，{len(have)} 张新图')
