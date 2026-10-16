#!/usr/bin/env python3
"""检查 data/twisters/NNN.json 是否合规：python3 data/twisters/check.py 001 002 ..."""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
L1 = 'Using the attached character sheet, keep Kron exactly as designed: same proportions, colours, face and quills, as a 25 cm plush toy.'
bad = 0
for n in sys.argv[1:]:
    todo = [x['w'] for x in json.load(open(os.path.join(H, f'todo-{n}.json')))]
    got = json.load(open(os.path.join(H, f'{n}.json')))
    if [x['w'] for x in got] != todo: print(n, '词表对不上'); bad += 1
    for x in got:
        p = []
        # 词头带 OCR 残留时写 "say"：句子里实际用的干净说法；带 ... 的词块逐段检查
        t = (x.get('say') or x['w']).lower().rstrip('.?!')
        if not all(seg.strip() in x['tw'].lower() for seg in re.split(r'\.{2,}|…', t) if seg.strip()): p.append('缺目标词')
        k = len(re.findall(r"[A-Za-z']+", x['tw']))
        if not 8 <= k <= 18: p.append(f'{k}词')
        if len(x['twc']) > 32: p.append(f'twc{len(x["twc"])}')
        if len(x['hint']) > 16: p.append(f'hint{len(x["hint"])}')
        ls = x['prompt'].split('\n')
        if len(ls) != 7 or ls[0] != L1 or not ls[6].startswith('A real-photography 4:3 landscape film still'): p.append('prompt格式')
        if not re.fullmatch(r'm(0[1-9]|1[0-6])', x['meme']): p.append('meme')
        # 词本身是 hedgehog 的那条可以出现这个词，其他一律不写
        if x['w'].lower() != 'hedgehog' and re.search(r'hedgehog|刺猬', json.dumps(x, ensure_ascii=False), re.I): p.append('禁词')
        if p: print(n, x['w'], p); bad += 1
print('问题', bad)
