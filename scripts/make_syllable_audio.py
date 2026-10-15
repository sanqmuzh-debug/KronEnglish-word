#!/usr/bin/env python3
"""给学习页的积木和整词生成读音（demo/audio/<词>.mp3、<词>-<第几块>.mp3）。

用开源的 Kokoro v0.19 (Apache-2.0) 直接按音标合成，不经过拼写猜读音，所以每块积木读的就是它在词里的音。
模型文件不进仓库：npm 包 n8n-nodes-ttsbro 里的 kokoro-int8-en-v0_19/ 目录（model.int8.onnx、voices.bin、tokens.txt）。
  pip install onnxruntime numpy soundfile;  ffmpeg 要在 PATH 里
  python3 scripts/make_syllable_audio.py --model <kokoro-int8-en-v0_19 目录> [--voice af_bella] [--out demo/audio]
"""
import argparse, json, os, re, subprocess, tempfile
import numpy as np, onnxruntime as ort, soundfile as sf

NAMES = 'af,af_bella,af_nicole,af_sarah,af_sky,am_adam,am_michael,bf_emma,bf_isabella,bm_george,bm_lewis'.split(',')
SR = 24000


class Kokoro:
    def __init__(self, d):
        self.vocab = {}
        for line in open(os.path.join(d, 'tokens.txt'), encoding='utf-8'):
            line = line.rstrip('\n')
            if line:
                sym, idx = line.rsplit(' ', 1)
                self.vocab[sym or ' '] = int(idx)
        self.voices = np.fromfile(os.path.join(d, 'voices.bin'), dtype=np.float32).reshape(len(NAMES), 511, 256)
        self.sess = ort.InferenceSession(os.path.join(d, 'model.int8.onnx'))

    def __call__(self, ps, voice, speed):
        bad = [c for c in ps if c not in self.vocab]
        if bad:
            raise ValueError(f'{ps}: 模型不认识 {bad}')
        ids = [self.vocab[c] for c in ps]
        style = self.voices[NAMES.index(voice)][len(ids)][None, :]
        out = self.sess.run(None, {'tokens': np.array([[0] + ids + [0]], dtype=np.int64), 'style': style,
                                   'speed': np.array([speed], dtype=np.float32)})[0]
        return np.asarray(out, dtype=np.float32).reshape(-1)


def stressed(ps):
    """单独读一块积木时给它重音，读得清楚；元音前面加 ˈ。"""
    if 'ˈ' in ps:
        return ps
    for i, c in enumerate(ps):
        if c in 'aeiouæɑɐɒɔəɚɛɜɪʊʌ':
            return ps[:i] + 'ˈ' + ps[i:]
    return ps


def tidy(a, th=0.012, pad=0.04):
    hit = np.where(np.abs(a) > th)[0]
    if len(hit):
        a = a[max(0, hit[0] - int(pad * SR)):hit[-1] + int(pad * SR)]
    fade = min(len(a) // 4, int(0.012 * SR))
    if fade:
        a[:fade] *= np.linspace(0, 1, fade)
        a[-fade:] *= np.linspace(1, 0, fade)
    return a / max(1e-6, np.abs(a).max()) * 0.89


def save_mp3(a, path):
    with tempfile.NamedTemporaryFile(suffix='.wav') as t:
        sf.write(t.name, a, SR)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', t.name, '-ac', '1', '-codec:a', 'libmp3lame', '-b:a', '48k', path], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True)
    ap.add_argument('--voice', default='af_bella')
    ap.add_argument('--out', default=os.path.join(os.path.dirname(__file__), '..', 'demo', 'audio'))
    ap.add_argument('--table', default=os.path.join(os.path.dirname(__file__), 'syllable_phonemes.json'))
    ap.add_argument('--syllables', help='用 scripts/syllabify.py 生成的 data/syllables.json 批量跑整本词库')
    ap.add_argument('--word-speed', type=float, default=0.85)
    ap.add_argument('--syl-speed', type=float, default=0.8)
    a = ap.parse_args()
    tts = Kokoro(a.model)
    os.makedirs(a.out, exist_ok=True)
    if a.syllables:
        table = {}
        for w, toks in json.load(open(a.syllables, encoding='utf-8'))['words'].items():
            syl = [x['ipa'].replace('ˌ', '').replace('ˈ', '') for t in toks for x in t]
            table[re.sub(r'[^a-z0-9]+', '-', w.lower()).strip('-')] = {'word': ' '.join(''.join(x['ipa'] for x in t) for t in toks), 'syl': syl}
    else:
        table = {k: v for k, v in json.load(open(a.table, encoding='utf-8')).items() if not k.startswith('_')}
    for w, e in table.items():
        save_mp3(tidy(tts(e['word'], a.voice, a.word_speed)), os.path.join(a.out, f'{w}.mp3'))
        for i, s in enumerate(e['syl']):
            save_mp3(tidy(tts(stressed(s), a.voice, a.syl_speed)), os.path.join(a.out, f'{w}-{i}.mp3'))
    print(f'{len(table)} 个词 → {a.out}')


if __name__ == '__main__':
    main()
