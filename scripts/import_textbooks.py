#!/usr/bin/env python3
"""把五个出版社的国内教材词表（data/textbooks/NNN.json）做成书架上的词书。

词表来源：国家中小学智慧教育平台的电子课本，每册书后的词汇表页 OCR 出来再人工清洗
（人名地名、英文释义续行、识别错字已去掉）。每册一本书，单元照课本。

同一个词在别的书里已经有了（Think、Power Up、IELTS、考纲词书或前面的教材），就直接用那一条：
同一个词共用一句绕口令、一张图、一套录音。没有的词新拆音节，记进 data/syllables-todo-textbooks.json，
录好 alex 音频放 R2（au/），网页走 /au/。

先跑 scripts/import_legacy.py，再跑这个；它把教材系列追加进 demo/shelf.js。

  python3 scripts/import_textbooks.py
"""
import glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import syllabify  # noqa: E402
from import_legacy import short_zh, strip_pos, slug  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS = os.path.join(ROOT, 'demo', 'books')
SRC = os.path.join(ROOT, 'data', 'textbooks')

SERIES = [('pep', '人教', '人教版'), ('bnu', '北师大', '北师大版'), ('wy', '外研', '外研版'), ('yl', '译林', '译林版'), ('sh', '沪教', '沪教版')]
CN = '一二三四五六七八九'
GRADE = {f'{CN[i]}年级': i + 1 for i in range(9)}


def level(b):
    """书名短称和书脊上的小字：三上 / 七下 / 必修一 / 选必二。"""
    if b['stage'] == '高中':
        n = re.search(r'第(.)册', b['grade'])[1]
        return ('选必' if '选择性' in b['grade'] else '必修') + n, ('选' if '选择性' in b['grade'] else '必') + str(CN.index(n) + 1)
    g, v = GRADE[b['grade']], b['vol'][0]
    return f'{CN[g - 1]}{v}', f'{g}{v}'


def book_id(sid, b):
    if b['stage'] == '高中':
        n = CN.index(re.search(r'第(.)册', b['grade'])[1]) + 1
        return f"{sid}-{'x' if '选择性' in b['grade'] else 'b'}{n}"
    return f"{sid}-{GRADE[b['grade']]}{'a' if b['vol'] == '上册' else 'b'}"


def main():
    shelf_js = os.path.join(ROOT, 'demo', 'shelf.js')
    s = open(shelf_js, encoding='utf-8').read()
    ids = {x[0] for x in SERIES}
    shelf = [sr for sr in json.loads(s[s.index('=') + 1:].rstrip().rstrip(';')) if sr['id'] not in ids]

    known = {}  # 小写词 -> 已有的那一条（先到先得）
    for sr in shelf:
        for b in sr['books']:
            for u in json.load(open(os.path.join(BOOKS, b['id'] + '.json'), encoding='utf-8'))['units']:
                for w in u['w']:
                    known.setdefault(w['w'].lower(), w)
    have = set(os.listdir(os.path.join(ROOT, 'demo', 'audio-fish')))
    d, review, todo = syllabify.cmu(), [], {}
    src = [json.load(open(f, encoding='utf-8')) for f in sorted(glob.glob(os.path.join(SRC, '*.json')))]

    def make(text, zh):
        old = known.get(text.lower())
        if old:
            w = dict(old)
            if zh:  # 释义用这本课本自己的
                w['zh'] = short_zh(zh)
                if strip_pos(zh) != w['zh']: w['zf'] = strip_pos(zh)
                else: w.pop('zf', None)
            return w
        toks = syllabify.run_word(text, d, review)
        bricks = [x for t in toks for x in t]
        w = {'w': text, 'syl': [x['t'] for x in bricks],
             'ipa': '/' + ' '.join(''.join(x['ipa'] for x in t) for t in toks).replace('ɹ', 'r') + '/',
             'zh': short_zh(zh), 'a': slug(text)}
        if strip_pos(zh) != w['zh']: w['zf'] = strip_pos(zh)
        if slug(text) + '.mp3' not in have:
            w['r'] = 1
            todo[text] = toks
        known[text.lower()] = w
        return w

    stats, mine_series = [], []
    for sid, pub, name in SERIES:
        sr = {'id': sid, 'name': name, 'books': []}
        mine = sorted((b for b in src if b['pub'] == pub), key=lambda b: (['小学', '初中', '高中'].index(b['stage']), book_id(sid, b)))
        for b in mine:
            bid = book_id(sid, b)
            lvl, mark = level(b)
            units = [{'n': u['n'], 't': u['t'], 'w': [make(x['w'], x['zh']) for x in u['words']]} for u in b['units']]
            with open(os.path.join(BOOKS, bid + '.json'), 'w', encoding='utf-8') as fp:
                json.dump({'id': bid, 'units': units}, fp, ensure_ascii=False, separators=(',', ':'))
            sr['books'].append({'id': bid, 'lvl': lvl, 'mark': mark, 'cover': os.path.exists(os.path.join(ROOT, 'demo', 'covers', bid + '.jpg')),
                                'units': [[u['n'], u['t'], len(u['w'])] for u in units]})
            ws = [w for u in units for w in u['w']]
            stats.append((bid, len(ws), sum('img' in w for w in ws), sum('r' in w and w['w'] in todo for w in ws)))
        mine_series.append(sr)
    shelf = mine_series + shelf  # 课本排在最前

    with open(shelf_js, 'w', encoding='utf-8') as fp:
        fp.write('/* scripts/import_legacy.py + scripts/import_textbooks.py 生成，别手改 */\nwindow.KRON_SHELF=')
        json.dump(shelf, fp, ensure_ascii=False, separators=(',', ':'))
        fp.write(';\n')
    json.dump({'words': todo}, open(os.path.join(ROOT, 'data', 'syllables-todo-textbooks.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('书         词数  有图  新词')
    for s in stats: print('%-10s %5d %5d %5d' % s)
    print(f'{len(todo)} 个新词要录 alex → data/syllables-todo-textbooks.json；{len(review)} 处拆音节要人看')


if __name__ == '__main__':
    main()
