#!/usr/bin/env python3
"""用 Fish Audio（alex 克隆声）给每个词的例句（绕口令）录音：<slug>-s.mp3，传进 R2 的 au/ 下，学习页从 /au/<slug>-s.mp3 读。

要在能连上 api.fish.audio 的电脑上跑（云端容器连不上）。只用标准库，密钥用法和 make_fish_audio.py 一样。
同一个词（按 slug 认）在哪本书里都是同一条绕口令，只录一遍。已经录过的跳过，断了可以接着跑。
  python3 scripts/make_sentence_audio.py --voice <reference_id> --keys-file ~/kron-audio/fish_keys.txt --out clips-s --shard 0/4
跑完用 scripts/trim_audio.sh 剪掉开头结尾的空白。
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_fish_audio import KeyRing, api_key, tts  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice', required=True)
    ap.add_argument('--model', default='s2.1-pro-free')
    ap.add_argument('--out', required=True)
    ap.add_argument('--keys-file')
    ap.add_argument('--shard', default='0/1')
    ap.add_argument('--speed', type=float, default=0.9)
    ap.add_argument('--only', type=int, help='只跑前 N 句（试听用）')
    a = ap.parse_args()
    si, sn = map(int, a.shard.split('/'))
    if a.keys_file:
        keys = [l.strip() for l in open(os.path.expanduser(a.keys_file)) if l.strip()]
        ring = KeyRing(keys[si % len(keys):] + keys[:si % len(keys)])
    else:
        ring = KeyRing([api_key()])
    sent = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'demo', 'books', '*.json'))):
        for u in json.load(open(f, encoding='utf-8'))['units']:
            for w in u['w']:
                if w.get('s'): sent.setdefault(w['a'], re.sub(r'[{}]', '', w['s']))
    items = sorted(sent.items())[:a.only] if a.only else sorted(sent.items())
    items = items[si::sn]
    os.makedirs(a.out, exist_ok=True)
    made = 0
    for slug, text in items:
        path = os.path.join(a.out, f'{slug}-s.mp3')
        if os.path.exists(path) and os.path.getsize(path) > 0: continue
        open(path, 'wb').write(tts(text, ring, a.voice, a.model, a.speed)); made += 1
        if made % 50 == 0: print(f'{made} 句', flush=True)
    print(f'新生成 {made} 句 → {a.out}（这一路共 {len(items)} 句）')


if __name__ == '__main__':
    main()
