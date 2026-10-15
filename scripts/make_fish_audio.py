#!/usr/bin/env python3
"""用 Fish Audio 批量生成积木和整词读音：每块积木按 CMU 音标（ARPAbet）读，不让模型自己猜。

要在能连上 api.fish.audio 的电脑上跑（云端容器连不上）。只用标准库。
  export FISH_API_KEY=...            # Fish 后台的 API key，不要写进仓库
  python3 scripts/make_fish_audio.py --voice <声音的 reference_id> [--model s1] [--only 20] [--out demo/audio-fish]
已经生成过的文件会跳过，断了可以接着跑。
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error

API = 'https://api.fish.audio/v1/tts'


def tts(text, key, voice, model, speed):
    body = json.dumps({'text': text, 'reference_id': voice, 'format': 'mp3', 'mp3_bitrate': 64, 'normalize': False,
                       'latency': 'normal', 'prosody': {'speed': speed}}).encode()
    req = urllib.request.Request(API, body, {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json', 'model': model})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 ** attempt * 2); continue
            raise SystemExit(f'Fish 返回 {e.code}: {e.read()[:300]!r}')
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(2 ** attempt * 2); continue
            raise


def phon(arpa):
    return f'<|phoneme_start|>{arpa}<|phoneme_end|>'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--voice', required=True)
    ap.add_argument('--model', default='s1')
    ap.add_argument('--syllables', default=os.path.join(os.path.dirname(__file__), '..', 'data', 'syllables.json'))
    ap.add_argument('--out', default=os.path.join(os.path.dirname(__file__), '..', 'demo', 'audio-fish'))
    ap.add_argument('--only', type=int, help='只跑前 N 个词（试听用）')
    ap.add_argument('--words', nargs='*', help='只跑这些词')
    ap.add_argument('--speed', type=float, default=0.9)
    a = ap.parse_args()
    key = os.environ.get('FISH_API_KEY') or sys.exit('先 export FISH_API_KEY=...')
    words = json.load(open(a.syllables, encoding='utf-8'))['words']
    items = [(w, t) for w, t in words.items() if not a.words or w in a.words]
    if a.only:
        items = items[:a.only]
    os.makedirs(a.out, exist_ok=True)
    made = 0
    for w, toks in items:
        slug = re.sub(r'[^a-z0-9]+', '-', w.lower()).strip('-')
        jobs = [(f'{slug}.mp3', ' '.join(phon(' '.join(x['arpa'] for x in t)) for t in toks))]
        jobs += [(f'{slug}-{i}.mp3', phon(x['arpa'])) for i, x in enumerate(x for t in toks for x in t)]
        for name, text in jobs:
            path = os.path.join(a.out, name)
            if os.path.exists(path) and os.path.getsize(path) > 0:
                continue
            open(path, 'wb').write(tts(text, key, a.voice, a.model, a.speed)); made += 1
        print(f'{w}: {len(jobs)} 段', flush=True)
    print(f'新生成 {made} 段 → {a.out}')


if __name__ == '__main__':
    main()
