#!/usr/bin/env python3
"""批量拆音节：拼写按自然拼读拆成积木，每块带自己的音标（ARPAbet 给 Fish Audio，IPA 给 Kokoro）。

做法：从 CMU 发音词典拿整词音标（词典里没有的英式拼写用 espeak 补），把字母和音素对齐，
按音素切音节（每个元音一个音节；VCV 里短元音重读时辅音归前面 lem|on，否则 ti|ger；
VCCV 在辅音之间切，blend 跟长元音时保留 se|cret；双写辅音拆开 rab|bit），再映射回字母。
对不齐的词标记出来交给人看，不瞎猜。

  pip install cmudict wordfreq espeakng-loader phonemizer-fork
  python3 scripts/syllabify.py 词1 词2 ...            # 看结果
  python3 scripts/syllabify.py --data data --out data/syllables.json
"""
import argparse, functools, glob, json, os, re, sys

VOWELS = {'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW'}
SHORT = {'AE', 'EH', 'IH', 'AA', 'AH', 'UH'}
ONSETS = {tuple(o.split()) for o in '''P L|P R|P Y|B L|B R|B Y|T R|T W|D R|D W|K L|K R|K W|K Y|G L|G R|G W|F L|F R|F Y|TH R|TH W|SH R|S P|S T|S K|S M|S N|S L|S W|S F|S P L|S P R|S T R|S K R|S K W|S K Y|S P Y|M Y|N Y|V Y|HH Y|L Y'''.split('|')}
# 字母块 -> 可能的音素（空串 = 不发音）
CONS = {
    'B': 'b bb', 'CH': 'ch tch t ti c cz', 'D': 'd dd ed ld', 'DH': 'th the', 'F': 'f ff ph gh', 'G': 'g gg gu gh gue',
    'HH': 'h wh', 'JH': 'j g dg dge ge gi d gg', 'K': 'k c ck ch q cc kh que', 'L': 'l ll', 'M': 'm mm mb mn lm',
    'N': 'n nn kn gn pn', 'NG': 'ng n ngue', 'P': 'p pp', 'R': 'r rr wr rh', 'S': 's ss c sc ce se ps st sw',
    'SH': 'sh ti ci ss s ch si ce sci', 'T': 't tt ed th pt bt', 'TH': 'th', 'V': 'v f vv ve', 'W': 'w u wh o',
    'Y': 'y i j', 'Z': 'z zz s ss se ze x', 'ZH': 's si g ge z ti',
}
PAIRS = {('K', 'S'): 'x cc cs', ('G', 'Z'): 'x', ('K', 'W'): 'qu', ('K', 'SH'): 'x', ('Y', 'UW'): 'u ue ew eu ewe ui iew eau ou',
         ('Y', 'UH'): 'u', ('Y', 'AH'): 'u io', ('W', 'AH'): 'o', ('AH', 'L'): 'le', ('AH', 'M'): 'm', ('AH', 'N'): 'n'}
PAIR_COST = {('AH', 'M'): 3.0, ('AH', 'N'): 3.0}
SILENT = {'e', 'h', 'gh', 'u', 'w', 'b', 'k', 'l', 't', 'ue', 'c'}
VOWEL_CHUNK = re.compile(r"[aeiouy]{1,3}(?:gh|w|r(?:e|r)?|l)?|[aeiou]?(?:igh|augh|ough|eigh|ear|our|oor|ar|er|ir|or|ur|yr)$|[aeiouy]{1,3}")
APOS = re.compile(r"[’']")


def cmu():
    import cmudict
    return cmudict.dict()


@functools.lru_cache(None)
def _espeak():
    import espeakng_loader
    from phonemizer.backend.espeak.wrapper import EspeakWrapper
    EspeakWrapper.set_library(espeakng_loader.get_library_path())
    EspeakWrapper.set_data_path(espeakng_loader.get_data_path())
    from phonemizer.backend import EspeakBackend
    return EspeakBackend('en-us', with_stress=True)


IPA2ARPA = [('aɪ', 'AY'), ('aʊ', 'AW'), ('eɪ', 'EY'), ('oʊ', 'OW'), ('ɔɪ', 'OY'), ('tʃ', 'CH'), ('dʒ', 'JH'), ('ɑːɹ', 'AA R'),
            ('ɔːɹ', 'AO R'), ('ɜː', 'ER'), ('ɚ', 'ER'), ('ɑː', 'AA'), ('ɔː', 'AO'), ('iː', 'IY'), ('uː', 'UW'), ('æ', 'AE'),
            ('ɐ', 'AH'), ('ʌ', 'AH'), ('ə', 'AH'), ('ɛ', 'EH'), ('ɪ', 'IH'), ('ᵻ', 'IH'), ('i', 'IY'), ('ʊ', 'UH'), ('ɑ', 'AA'),
            ('ɔ', 'AO'), ('o', 'OW'), ('e', 'EH'), ('a', 'AE'), ('u', 'UW'),
            ('ŋ', 'NG'), ('θ', 'TH'), ('ð', 'DH'), ('ʃ', 'SH'), ('ʒ', 'ZH'), ('ɹ', 'R'), ('ɾ', 'T'), ('ʔ', 'T'), ('ɡ', 'G'), ('j', 'Y'),
            ('b', 'B'), ('d', 'D'), ('f', 'F'), ('h', 'HH'), ('k', 'K'), ('l', 'L'), ('m', 'M'), ('n', 'N'), ('p', 'P'),
            ('s', 'S'), ('t', 'T'), ('v', 'V'), ('w', 'W'), ('z', 'Z')]


def espeak_arpa(word):
    return ipa_to_arpa(_espeak().phonemize([word], strip=True)[0])


def ipa_to_arpa(ps):
    out, stress, i = [], '0', 0
    while i < len(ps):
        if ps[i] in 'ˈˌ':
            stress = '1' if ps[i] == 'ˈ' else '2'; i += 1; continue
        for ipa, ar in IPA2ARPA:
            if ps.startswith(ipa, i):
                for a in ar.split():
                    out.append(a + stress if a in VOWELS else a)
                    if a in VOWELS: stress = '0'
                i += len(ipa); break
        else:
            i += 1
    return out


def options(letters):
    """[(字母块, 音素元组, 代价)]"""
    opts = []
    for ph, sp in CONS.items():
        for s in sp.split():
            opts.append((s, (ph,), 1.0 if len(s) > 1 or s in 'bdfklmnprstvz' else 1.2))
    for ph, sp in PAIRS.items():
        for s in sp.split():
            opts.append((s, ph, PAIR_COST.get(ph, 1.1)))
    for s in SILENT:
        opts.append((s, (), 1.6))
    return opts


OPTS = options('')


def align(word, phones):
    """字母和音素对齐，返回 [(字母块, [音素])] 或 None。"""
    w = word.lower()
    base = [re.sub(r'\d', '', p) for p in phones]
    n, m = len(w), len(base)
    INF = float('inf')
    best = [[INF] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    best[0][0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            c = best[i][j]
            if c == INF:
                continue
            def go(L, P, cost):
                ni, nj = i + L, j + P
                if c + cost < best[ni][nj]:
                    best[ni][nj] = c + cost; back[ni][nj] = (i, j)
            for s, ph, cost in OPTS:
                if w.startswith(s, i) and tuple(base[j:j + len(ph)]) == ph:
                    go(len(s), len(ph), cost)
            # 元音字母块 -> 一个元音（可带 R / Y UW）
            if j < m and base[j] in VOWELS:
                for L in range(1, 5):
                    ch = w[i:i + L]
                    if len(ch) < L or not re.fullmatch(r"[aeiouy]{1,3}(?:r|w|gh|l|ugh)?(?<=r)e?|[aeiouy]{1,3}(?:w|gh|l|ugh)?", ch) or not re.search('[aeiouy]', ch):
                        continue
                    if ch[-1] == 'e' and len(ch) > 1 and ch[-2] == 'r' and i + L != n:
                        continue  # are/ire/ore 只在词尾
                    has_r = 'r' in ch[1:]
                    go(L, 1, 1.0 + 0.3 * (L - 1) + (0.8 if has_r and base[j] != 'ER' else 0) + (0.3 if ch[0] == 'y' and L > 1 else 0))  # play|er 不是 pla|yer
                    if has_r and j + 1 < m and base[j + 1] == 'R':
                        go(L, 2, 1.1 + 0.3 * (L - 1))
            if j < m and base[j] == 'ER':  # hurry、arrest 的 urr/arr，centre 的词尾 re
                for ch in ('urr', 'arr', 'err', 'irr', 'orr'):
                    if w.startswith(ch, i): go(3, 1, 1.4)
                if w.startswith('re', i) and i + 2 == n: go(2, 1, 1.2)
    if best[n][m] == INF:
        return None
    path, i, j = [], n, m
    while (i, j) != (0, 0):
        pi, pj = back[i][j]
        path.append((word[pi:i], list(phones[pj:j])))
        i, j = pi, pj
    return path[::-1]


def is_vowel(p):
    return re.sub(r'\d', '', p) in VOWELS


COMPOUND_WORDS = None


@functools.lru_cache(None)
def zipf(w):
    from wordfreq import zipf_frequency
    return zipf_frequency(w, 'en')


def compound_cut(word, phones, d):
    """weekend = week + end：两半都是词典里的词，而且两半的读音拼起来就是整词读音，就在两半之间切。"""
    w = word.lower()
    bare = lambda ps: [re.sub(r'\d', '', p) for p in ps]
    whole = bare(phones)
    for i in range(3, len(w) - 2):
        a, b = w[:i], w[i:]
        if a in d and b in d and min(zipf(a), zipf(b)) >= 3.5 and any(bare(x) + bare(y) == whole for x in d[a] for y in d[b]):
            return i
    return None


def syllabify_word(word, phones, d=None):
    units = align(word, phones)
    if units is None:
        return None
    # 每个单元拆成 (字母, 音素)；含元音的单元是音节核
    nuclei = [k for k, (_, ps) in enumerate(units) if any(is_vowel(p) for p in ps)]
    if len(nuclei) <= 1:
        return [{'t': word, 'ph': list(phones)}]
    cuts = []  # (单元下标, 是否双写拆开)
    for a, b in zip(nuclei, nuclei[1:]):
        mid = [k for k in range(a + 1, b) if units[k][1]]  # 发音的辅音单元
        vprev = [p for p in units[a][1] if is_vowel(p)][-1]
        vb = re.sub(r'\d', '', vprev)
        short = vb in SHORT and not (vb == 'AA' and 'o' not in units[a][0].lower())  # father 的 a 不算短元音
        short_stressed = short and vprev[-1] in '12'
        if not mid:
            cuts.append((b, False)); continue
        if len(mid) == 1:
            k = mid[0]
            letters = units[k][0].lower()
            if len(letters) == 2 and letters[0] == letters[1] and letters[0] not in 'aeiou':
                cuts.append((k, True))
            elif letters.startswith('x'):
                cuts.append((k + 1, False))  # ex|ci|ting
            elif re.search('[aeiouy]', letters):
                cuts.append((k, False))  # pe|ti|tion：ti/ci/si 带着后面的元音

            elif short_stressed and units[a][1][-1:] and is_vowel(units[a][1][-1]):
                cuts.append((k + 1, False))
            else:
                cuts.append((k, False))
            continue
        cons = [tuple(units[k][1]) for k in mid]
        flat = lambda ks: tuple(p for k in ks for p in units[k][1])
        # 至少留一个辅音给前面（闭音节），除非长元音后面跟的是 blend
        start = 1
        if not short_stressed and flat(mid) in ONSETS and flat(mid)[0] != 'S':
            start = 0
        for s in range(start, len(mid)):
            if len(mid[s:]) == 1 or flat(mid[s:]) in ONSETS:
                if flat(mid[s:])[0] == 'S' and short and s < len(mid) - 1:
                    continue  # mis|take、bas|ket：s 跟前面
                cuts.append((mid[s], False)); break
        else:
            cuts.append((mid[-1], False))
    cpos = compound_cut(word, phones, d) if d is not None else None
    if cpos is not None:
        starts, pos = [], 0
        for t, _ in units:
            starts.append(pos); pos += len(t)
        if cpos in starts:
            ck = starts.index(cpos)
            # 换掉落在同一对音节核之间的那一刀
            for n, (a, b) in enumerate(zip(nuclei, nuclei[1:])):
                if a < ck <= b:
                    cuts[n] = (ck, False)
    # mem|o|ra|ble、gi|raffe：元音后的 r 后面紧跟元音时，r 归后一块
    units = [list(u) for u in units]
    for a, b in zip(nuclei, nuclei[1:]):
        t, ps = units[a]
        if b == a + 1 and len(t) > 1 and t[-1].lower() == 'r' and ps:
            if ps[-1] == 'R':
                units[a] = [t[:-1], ps[:-1]]; units[b] = ['r' + units[b][0] if t[-1] == 'r' else t[-1] + units[b][0], ['R'] + units[b][1]]
            elif re.sub(r'\d', '', ps[-1]) == 'ER':
                units[a] = [t[:-1], ps[:-1] + ['AH' + ps[-1][-1]]]; units[b] = [t[-1] + units[b][0], ['R'] + units[b][1]]
    syls, cur_t, cur_p, k0 = [], '', [], 0
    for k, (t, ps) in enumerate(units):
        cut = next((c for c in cuts if c[0] == k), None)
        if cut and cut[1]:  # 双写辅音：一半给前面一半给后面，音素两边都读
            cur_t += t[0]; cur_p += ps
            syls.append({'t': cur_t, 'ph': cur_p}); cur_t, cur_p = t[1:], list(ps); continue
        if cut and (cur_t and any(is_vowel(p) for p in cur_p)):
            syls.append({'t': cur_t, 'ph': cur_p}); cur_t, cur_p = '', []
        cur_t += t; cur_p += ps
    syls.append({'t': cur_t, 'ph': cur_p})
    # 不发音的单元（结尾 e 等）粘在前一块上
    out = []
    for s in syls:
        if out and not any(is_vowel(p) for p in s['ph']):
            out[-1]['t'] += s['t']; out[-1]['ph'] += s['ph']
        else:
            out.append(s)
    return out


ARPA2IPA = {'AA': 'ɑː', 'AE': 'æ', 'AO': 'ɔː', 'AW': 'aʊ', 'AY': 'aɪ', 'EH': 'ɛ', 'EY': 'eɪ', 'IH': 'ɪ', 'OW': 'oʊ', 'OY': 'ɔɪ',
            'UH': 'ʊ', 'UW': 'uː', 'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'F': 'f', 'G': 'ɡ', 'HH': 'h', 'JH': 'dʒ', 'K': 'k',
            'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'P': 'p', 'R': 'ɹ', 'S': 's', 'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'V': 'v',
            'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ'}


def to_ipa(phones):
    out = ''
    for p in phones:
        b, st = re.sub(r'\d', '', p), (p[-1] if p[-1].isdigit() else '')
        if b == 'AH': v = 'ʌ' if st in '12' and st else 'ə'
        elif b == 'ER': v = 'ɜː' if st in '12' and st else 'ɚ'
        elif b == 'IY': v = 'iː' if st in '12' and st else 'i'
        else: v = ARPA2IPA[b]
        out += ('ˈ' if st == '1' else 'ˌ' if st == '2' else '') + v if b in VOWELS else v
    return out


LETTERS = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ', ['EY1', 'B IY1', 'S IY1', 'D IY1', 'IY1', 'EH1 F', 'JH IY1', 'EY1 CH', 'AY1', 'JH EY1',
    'K EY1', 'EH1 L', 'EH1 M', 'EH1 N', 'OW1', 'P IY1', 'K Y UW1', 'AA1 R', 'EH1 S', 'T IY1', 'Y UW1', 'V IY1', 'D AH1 B AH0 L Y UW0', 'EH1 K S', 'W AY1', 'Z IY1']))


@functools.lru_cache(None)
def overrides():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'syllable_overrides.json')
    return {k: v for k, v in json.load(open(p, encoding='utf-8')).items() if not k.startswith('_')}


def run_word(word, d, review):
    toks = re.findall(r"[A-Za-zÀ-ÿ]+", APOS.sub('', re.sub(r'\(.*?\)', ' ', word)))
    res = []
    after_dot = re.search(r'\b[ap]\.m\.', word)
    for t in toks:
        key = t.lower()
        src = 'cmu'
        if key in overrides():  # 手写的拆法
            res.append([{'t': x, 'arpa': ar, 'ipa': to_ipa(ar.split())} for x, ar in overrides()[key]]); continue
        if (t.isupper() and len(t) <= 4 and t not in ('I', 'A')) or (len(t) == 1 and (after_dot or '-' in word)):
            # 缩写一个字母一块，读字母名：G|P|S、T-shirt 的 T、p.m.
            res.append([{'t': c, 'arpa': LETTERS[c.upper()], 'ipa': to_ipa(LETTERS[c.upper()].split())} for c in t]); continue
        if key in d:
            # 有几种读法时挑音节数最接近拼写的（interesting 读 in-ter-est-ing 而不是 in-trest-ing）
            groups = len(re.findall(r'[aeiouy]+', re.sub(r'e$', '', key))) or 1
            phones = min(d[key], key=lambda ps: abs(sum(is_vowel(p) for p in ps) - groups))
        else:
            phones, src = espeak_arpa(key), 'espeak'
        syl = syllabify_word(t, phones, d) if re.fullmatch('[A-Za-z]+', t) else None
        if syl is None:
            review.append({'word': word, 'token': t, 'why': '字母和音标对不上', 'phones': ' '.join(phones)})
            syl = [{'t': t, 'ph': list(phones)}]
        elif len(syl) > 1 and any(not re.search('[aeiouyAEIOUY]', x['t']) for x in syl[1:]):
            merged = [syl[0]]
            for x in syl[1:]:  # opti|mis|m 的 m 并回前一块：op|ti|mism
                if re.search('[aeiouyAEIOUY]', x['t']): merged.append(x)
                else: merged[-1] = {'t': merged[-1]['t'] + x['t'], 'ph': merged[-1]['ph'] + x['ph']}
            syl = merged
        if any(len(re.findall(r'[aeiouy]+', re.sub(r'(?<=[^aeiouy])(e|es|ed)$', '', x['t'].lower()))) > 1 for x in syl):
            review.append({'word': word, 'token': t, 'why': '读音比拼写少音节（中间有字母不发音）', 'split': '|'.join(x['t'] for x in syl)})
        if src == 'espeak':
            review.append({'word': word, 'token': t, 'why': '词典里没有（英式拼写或拼错了？），用 espeak 推的音标', 'phones': ' '.join(phones)})
        res.append([{'t': s['t'], 'arpa': ' '.join(s['ph']), 'ipa': to_ipa(s['ph'])} for s in syl])
    return res


def book_words(data_dir):
    ws = set()
    def walk(x):
        if isinstance(x, dict):
            if 'boxes' in x and ('text' in x or 'word' in x):
                ws.add(x.get('text') or x.get('word'))
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    for f in sorted(glob.glob(os.path.join(data_dir, '*-vocab.json'))):
        walk(json.load(open(f, encoding='utf-8')))
    return sorted(ws, key=str.lower)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('words', nargs='*')
    ap.add_argument('--data')
    ap.add_argument('--out')
    a = ap.parse_args()
    d = cmu()
    words = a.words or book_words(a.data)
    review, out = [], {}
    for w in words:
        out[w] = run_word(w, d, review)
    seen, uniq = set(), []
    for r in review:  # 同一个词只列一次
        if (r['word'], r['token']) not in seen:
            seen.add((r['word'], r['token'])); uniq.append(r)
    review = uniq
    if a.out:
        json.dump({'words': out, 'review': review}, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print(f'{len(out)} 个词，{len(review)} 处要人看 → {a.out}')
    else:
        for w, toks in out.items():
            print(w, '  ', ' '.join('|'.join(s['t'] for s in tok) for tok in toks), '  ', ' '.join('·'.join(s['ipa'] for s in tok) for tok in toks))
        for r in review: print('  !', r)


if __name__ == '__main__':
    main()
