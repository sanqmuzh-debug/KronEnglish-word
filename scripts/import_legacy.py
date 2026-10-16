#!/usr/bin/env python3
"""把老版 KronWord 的数据转成新版书架用的词书：demo/books/<书>.json + demo/shelf.js。

老版数据在 Kron 的 Mac：/Users/kron/KronEnglish/src/data/（kronword-rhyme-sentences.json、
kronword-batch-pool.json、各本 *-vocab.json）。图片名单是老版 public/assets/word/images 的 ls 结果，
图片本身在 R2 桶 kronword-images，网页经 /img/<文件名> 读（functions/img/[[path]].js，过登录门禁）。

每个词：音节积木用 scripts/syllabify.py 重新拆（CMU 美式），例句只用老版剧情长句 + 中文，
Kron 脑洞用 mindSpark；老版没有的词退回教材自带的例句和 kronTip。
13000 考纲词按考试分 7 本书，每个词放进它最简单的那本，按老版排序每 50 词一个单元。

  python3 scripts/import_legacy.py --legacy <老版 src/data> --images <图片名单.txt>
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import syllabify  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'demo', 'books')

# 新版书 id、老版词表、老版图片/句子的前缀
TEXTBOOKS = {
    'think': ('Think', [('th0', 'th0-vocab.json', 'th0', 'Starter', 'S'), ('th1', 'th1-vocab.json', 'th1', '1', '1'),
                        ('th2', 'th2-vocab.json', 'th2', '2', '2'), ('think-l3', 'think-l3-vocab.json', 'th3', '3', '3'),
                        ('th4', 'th4-vocab.json', 'th4', '4', '4'), ('th5', 'th5-vocab.json', 'th5', '5', '5')]),
    'pu': ('Power Up', [('pu0', 'pu0-vocab.json', 'pu0', 'Start Smart', 'S'), ('pu1', 'pu1-vocab.json', 'pu1', '1', '1'),
                        ('pu2', 'pu2-vocab.json', 'pu2', '2', '2'), ('pu3', 'pu3-vocab.json', 'pu3', '3', '3'),
                        ('pu4', 'pu4-vocab.json', 'pu4', '4', '4')]),
    'ielts': ('IELTS', [('ielts', 'ielts-vocab.json', 'ielts', 'Foundation', 'F'),
                        ('ielts-adv', 'ielts-adv-vocab.json', 'ielts-adv', 'Advanced', 'A')]),
}
# 考纲词书：从易到难，一个词进它出现的最简单那本
EXAMS = [
    ('ex-zk', '中考', {'ZHONGKAO', '中考'}),
    ('ex-gk', '高考', {'GAOKAO', '高考3500', '高考高频', 'PEP', 'BNU', 'WY', 'SH', 'YL', 'NCE'}),
    ('ex-cet4', '四级', {'CET4'}),
    ('ex-cet6', '六级', {'CET6'}),
    ('ex-ky', '考研', {'KAOYAN', '考研2025'}),
    ('ex-tem', '专四专八', {'TEM4', 'TEM8'}),
    ('ex-abroad', '出国', None),  # 托福、SAT、GRE、GMAT、PTE 等其余全部
]
UNIT_SIZE = 50
PLACEHOLDER = 'hilariously engaged in an exaggerated comedy scene'

slug = lambda s: re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
clean = lambda s: re.sub(r'\s+', ' ', (s or '').strip())


def short_zh(zh):
    """卡片上只放第一个意思：「丰富的， 富裕的； 大量的」→「丰富的」。"""
    z = re.split(r'[；;]', clean(zh))[0].strip()
    if len(z) > 8: z = re.split(r'[，,/、]', z)[0].strip() or z
    return z


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--legacy', required=True)
    ap.add_argument('--images', required=True)
    a = ap.parse_args()
    L = lambda f: json.load(open(os.path.join(a.legacy, f), encoding='utf-8'))

    images = {l.strip() for l in open(a.images, encoding='utf-8') if l.strip().endswith('.webp')}
    img_by = {}  # (前缀, 词) -> 图片名；教材图名是 <前缀>-uNN-<词>.webp
    for n in sorted(images):
        m = re.match(r'(ielts-adv|ielts|pu\d|th\d)-u\d+-(.+)\.webp$', n)
        if m: img_by.setdefault((m[1], m[2]), n)
    rhyme = L('kronword-rhyme-sentences.json')['items']
    r_by, r_word = {}, {}
    for k, it in rhyme.items():
        m = re.match(r'(ielts-adv|ielts|pu\d|th\d)-u\d+-(.+)$', k)
        if m: r_by.setdefault((m[1], m[2]), it)
        if k.startswith('kw-'): r_word.setdefault(it['targetWord'].lower(), it)
    pool = L('kronword-batch-pool.json')['batches']
    kw = {}
    for b in pool:
        for it in b['items']:
            kw.setdefault(it['word'].lower(), it)

    d = syllabify.cmu()
    review = []
    have = set(os.listdir(os.path.join(ROOT, 'demo', 'audio-fish')))
    todo = {}

    def make(text, zh, ipa, hint, sent, sent_cn, r, img):
        toks = syllabify.run_word(text, d, review)
        if slug(text) + '.mp3' not in have:  # 没有 alex 录音的词：记下来给 make_fish_audio.py，录好放 R2，网页走 /au/
            todo[text] = toks
        bricks = [x for t in toks for x in t]
        w = {'w': text, 'syl': [x['t'] for x in bricks], 'ipa': ipa or '/' + ' '.join('·'.join(x['ipa'] for x in t) for t in toks).replace('·', '') + '/',
             'zh': short_zh(zh), 'a': slug(text)}
        if slug(text) + '.mp3' not in have: w['r'] = 1
        if clean(zh) != w['zh']: w['zf'] = clean(zh)
        if r and PLACEHOLDER in (r.get('sentence') or ''):  # 老版约 1500 词只有模板占位句，不拿来用
            if not img and r.get('image'): img = os.path.basename(r['image'])
            r = None
        if r:  # 老版剧情长句 + mindSpark
            sent, sent_cn, hint = r.get('sentence') or sent, r.get('sentenceCn') or sent_cn, r.get('mindSpark') or hint
            if not img and r.get('image'): img = os.path.basename(r['image'])
        if hint: w['hint'] = clean(hint)
        if sent: w['s'] = clean(sent)
        if sent_cn: w['sc'] = clean(sent_cn)
        if img and img in images: w['img'] = img
        return w

    os.makedirs(OUT, exist_ok=True)
    shelf, stats = [], []
    for sid, (sname, books) in TEXTBOOKS.items():
        sr = {'id': sid, 'name': sname, 'books': []}
        for bid, f, pre, lvl, mark in books:
            units, seen = [], set()
            for key, u in L(f).items():
                ids = tuple(x['id'] for x in u.get('words', []))
                if not ids or ids in seen: continue
                seen.add(ids)
                ws = []
                for x in u['words']:
                    s = slug(x['text'])
                    r = r_by.get((pre, s)) or r_word.get(x['text'].lower())
                    img = img_by.get((pre, s))
                    ws.append(make(x['text'], x.get('translation'), x.get('ipa'), x.get('kronTip'), x.get('example') or x.get('sentence'),
                                   x.get('exampleTranslation') or x.get('sentenceZh'), r, img))
                name = u.get('unitName') or key
                title = u.get('title') or ''
                title = re.sub(r'^(Unit \d+|Welcome( Unit)?)\s*[·:：-]\s*', '', title)
                units.append({'n': name, 't': title if title != name else '', 'w': ws})
            write(bid, units)
            sr['books'].append({'id': bid, 'lvl': lvl, 'mark': mark, 'cover': sid != 'ielts',
                                'units': [[u['n'], u['t'], len(u['w'])] for u in units]})
            stats.append(report(bid, units))
        shelf.append(sr)

    # 考纲词书
    groups = {e[0]: [] for e in EXAMS}
    for b in pool:
        for it in b['items']:
            ex = set(it.get('exams') or [])
            gid = next((g for g, _, tags in EXAMS if tags is None or ex & tags), 'ex-abroad')
            groups[gid].append(it)
    sr = {'id': 'exam', 'name': '考试', 'books': []}
    for gid, name, _ in EXAMS:
        items = sorted(groups[gid], key=lambda it: it['globalIndex'])
        units = []
        for i in range(0, len(items), UNIT_SIZE):
            ws = []
            for it in items[i:i + UNIT_SIZE]:
                r = rhyme.get(it['filename'][:-5]) or r_word.get(it['word'].lower())
                ws.append(make(it['word'], it.get('trans'), '', '', '', '', r, it['filename']))
            units.append({'n': f'Unit {len(units) + 1}', 't': '', 'w': ws})
        write(gid, units)
        sr['books'].append({'id': gid, 'lvl': name, 'mark': name[:1], 'cover': False,
                            'units': [[u['n'], u['t'], len(u['w'])] for u in units]})
        stats.append(report(gid, units))
    shelf.append(sr)

    with open(os.path.join(ROOT, 'demo', 'shelf.js'), 'w', encoding='utf-8') as fp:
        fp.write('/* scripts/import_legacy.py 生成，别手改 */\nwindow.KRON_SHELF=')
        json.dump(shelf, fp, ensure_ascii=False, separators=(',', ':'))
        fp.write(';\n')
    json.dump({'words': todo}, open(os.path.join(ROOT, 'data', 'syllables-todo.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'{len(todo)} 个词还没有 alex 录音 → data/syllables-todo.json')
    print('书      词数  有图  有长句  有脑洞')
    for s in stats: print('%-10s %5d %5d %6d %6d' % s)
    print(f'{len(review)} 处拆音节要人看（syllabify 的 review）')


def write(bid, units):
    with open(os.path.join(OUT, bid + '.json'), 'w', encoding='utf-8') as fp:
        json.dump({'id': bid, 'units': units}, fp, ensure_ascii=False, separators=(',', ':'))


def report(bid, units):
    ws = [w for u in units for w in u['w']]
    return (bid, len(ws), sum('img' in w for w in ws), sum('sc' in w for w in ws), sum('hint' in w for w in ws))


if __name__ == '__main__':
    main()
