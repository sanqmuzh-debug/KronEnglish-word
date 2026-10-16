#!/usr/bin/env python3
"""按版面坐标重配中文释义：OCR 每行带 (x, y)，英文词和同一行、右边最近的中文才是一对。
原来按出现顺序配对，遇到漏识别的中文行（北师大小学最多）就整列错位。
  python3 scripts/textbook_ocr/rezh.py <ocrtxt 目录>   # 改 data/textbooks/NNN.json 的 zh
找不到同行中文的词把 zh 清空（导入时已有的词沿用旧释义）。"""
import difflib, glob, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CJK = re.compile(r'[一-鿿]')
# l/i 是 OCR 最常混的一对，比较时当成一样
norm = lambda t: re.sub(r'[^a-z]', '', t.lower()).replace('l', 'i')

def rows(path):
    out = []  # (english_norm, zh or '')
    for page in open(path, encoding='utf-8').read().split('### ')[1:]:
        L = []
        for ln in page.split('\n')[1:]:
            m = re.match(r'([\d.]+) ([\d.]+) (.*)', ln)
            if m: L.append((float(m[1]), float(m[2]), m[3].strip()))
        zh = [l for l in L if CJK.search(l[2])]
        for x, y, t in sorted((l for l in L if not CJK.search(l[2]) and re.search('[A-Za-z]{2}', l[2])), key=lambda l: (l[0] > .45, l[1])):
            c = [z for z in zh if 0 < z[0] - x < .36 and abs(z[1] - y) < .013]
            out.append((norm(t), min(c, key=lambda z: z[0] - x)[2] if c else ''))
    return out

# 对版面时顺带看出来的词头识别错（书号, 错词头）-> 正确词头；以及配错的个别释义
HEAD = {('021', 'river'): 'driver', ('024', 'river'): 'driver', ('023', 'repay'): 'ready', ('023', 'boy'): 'body',
        ('023', 'have a cola'): 'have a cold', ('023', 'have d headache'): 'have a headache', ('026', 'night'): 'height',
        ('022', 'Being roast luck'): 'Beijing roast duck'}
ZH = {('025', 'cloudy'): '多云的'}
stat = []
for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'textbooks', '*.json'))):
    n = os.path.basename(f)[:3]; o = os.path.join(sys.argv[1], n + '.ocr')
    if not os.path.exists(o): continue
    R = rows(o); b = json.load(open(f, encoding='utf-8')); ch = miss = tot = 0; i = 0
    W = [x for u in b['units'] for x in u['words']]
    for x in W: x['w'] = HEAD.get((n, x['w']), x['w'])
    for k, x in enumerate(W):
        if True:
            tot += 1; w = norm(x['w'])
            # 近处找最像的（OCR 拼错、越远越不信）；近处没有才跳去远处一模一样的（跨过课文页）
            best, bj = 0, None
            for j in range(i, min(len(R), i + 40)):
                r = difflib.SequenceMatcher(None, w, R[j][0]).ratio() - .006 * (j - i)
                if r > best: best, bj = r, j
            if best < .78:
                bj = next((j for j in range(i, len(R)) if R[j][0] == w), None)
                # 跳过去要下一个词也紧跟着对上，免得跳进别的词表
                if bj is not None and k + 1 < len(W) and norm(W[k + 1]['w']) not in [r[0] for r in R[bj + 1:bj + 4]]: bj = None
            if bj is None:
                miss += 1
                if os.environ.get("DBG") == n: print("miss", x["w"], i)
                continue
            if os.environ.get("DBG") == n: print(x["w"], bj, R[bj])
            i = bj + 1; z = R[bj][1]
            z = re.sub(r'\s+|\d+$', '', z)  # 去掉粘上的页码
            if z != re.sub(r'\s+', '', x['zh']): x['new'] = z; ch += 1
    # 大半词都对上了才说明这本书的版面是这种排法，才改
    ok = miss < tot * .45
    newzh = {x['new'] for x in W if x.get('new')}
    for x in W:
        z = x.pop('new', None)
        # 同行没有中文：旧释义要是别的词的（错位来的）才清空，否则留着
        if ok and z is not None and (z or x['zh'] in newzh): x['zh'] = z
        x['zh'] = ZH.get((n, x['w']), x['zh'])
    if not ok: ch = 0
    json.dump(b, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    stat.append((n, b['pub'], b['grade'], b['vol'], tot, ch, miss))
for s in stat:
    if s[5] > s[4] * .1 or s[6] > s[4] * .45: print('%s %s %s%s 词%d 改%d 没对上%d' % s)
print('共改', sum(s[5] for s in stat), '处')
