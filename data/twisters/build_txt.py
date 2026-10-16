#!/usr/bin/env python3
"""把写好的批次拼成能直接贴进 Flow Agent 的纯文本：python3 data/twisters/build_txt.py <输出目录>
每批一个 NNN.txt：第一行合集名，下面每张图一段（第一行文件名，后面是提示词，固定的第一句在 Agent Instructions 里，不重复）。"""
import glob, json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
slug = lambda t: re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for f in sorted(glob.glob(os.path.join(H, '[0-9][0-9][0-9].json'))):
    n = os.path.basename(f)[:3]
    items = json.load(open(f, encoding='utf-8'))
    body = '\n\n'.join('tw-' + slug(x['w']) + '\n' + '\n'.join(x['prompt'].split('\n')[1:]) for x in items)
    open(os.path.join(out, n + '.txt'), 'w', encoding='utf-8').write(f'Collection: Kron Word {n}\n\n{body}\n')
    print(n)
