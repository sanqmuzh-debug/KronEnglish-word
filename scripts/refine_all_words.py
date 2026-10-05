#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Standalone Refiner for KronEnglish-word.
Refines all HTML modules in public/word to guarantee 100% compliance.
"""

import os
import re
import json
import glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WORD_DIR = os.path.join(BASE_DIR, "public", "word")

GLOBAL_TRANSLATIONS = {}
for p in glob.glob(os.path.join(DATA_DIR, "*vocab*.json")):
    try:
        with open(p, "r", encoding="utf-8") as fp:
            d = json.load(fp)
        if isinstance(d, dict):
            for uk, u in d.items():
                if not isinstance(u, dict): continue
                for w in u.get("words", []) + u.get("phrases", []):
                    t = w.get("text") or w.get("word")
                    tr = w.get("translation") or w.get("meaning")
                    if t and tr and t.lower() not in GLOBAL_TRANSLATIONS:
                        GLOBAL_TRANSLATIONS[t.lower()] = tr
    except Exception:
        pass

VOWELS = "aeiouyAEIOUY"
ONSET_3 = ["spl", "spr", "str", "scr", "shr", "squ"]
ONSET_2 = [
    "bl", "cl", "fl", "gl", "pl", "sl",
    "br", "cr", "dr", "fr", "gr", "pr", "tr",
    "sc", "sk", "sm", "sn", "sp", "st", "sw", "tw", "dw",
    "th", "sh", "ch", "wh", "ph", "wr", "kn", "gn", "qu"
]
PREFIXES = [
    "un", "re", "dis", "mis", "pre", "pro", "sub", "inter", "trans", "over", "under",
    "in", "im", "il", "ir", "con", "com", "col", "cor", "ex", "en", "em", "de",
    "anti", "non", "super", "tele", "auto", "micro", "multi"
]
SUFFIXES = [
    "tion", "sion", "ment", "ness", "able", "ible", "ful", "less", "ly",
    "ing", "ed", "er", "or", "ist", "ism", "ity", "ty", "ous", "ious",
    "ic", "al", "ive", "est", "ance", "ence", "ship", "hood"
]

MANUAL_CHUNKS = {
    "instrument": ["in", "stru", "ment"],
    "play": ["pl", "ay"],
    "have": ["h", "ave"],
    "give": ["g", "ive"],
    "live": ["l", "ive"],
    "love": ["l", "ove"],
    "come": ["c", "ome"],
    "some": ["s", "ome"],
    "done": ["d", "one"],
    "gone": ["g", "one"],
    "guitar": ["gui", "tar"],
    "pianist": ["pi", "an", "ist"],
    "brazil": ["Bra", "zil"],
    "spanish": ["Span", "ish"],
    "together": ["to", "geth", "er"],
    "supermarket": ["su", "per", "mar", "ket"],
    "roommate": ["room", "mate"],
    "smartphone": ["smart", "phone"],
    "headphones": ["head", "phones"],
    "competition": ["com", "pe", "ti", "tion"],
    "expensive": ["ex", "pen", "sive"],
    "information": ["in", "for", "ma", "tion"],
    "technology": ["tech", "nol", "o", "gy"],
    "traditional": ["tra", "di", "tion", "al"],
    "archaeologist": ["ar", "chae", "ol", "o", "gist"],
    "nanotechnology": ["nano", "tech", "nol", "o", "gy"],
    "microscope": ["mi", "cro", "scope"],
    "laboratory": ["lab", "o", "ra", "to", "ry"],
    "documentary": ["doc", "u", "men", "ta", "ry"],
    "science": ["sci", "ence"],
    "biology": ["bi", "ol", "o", "gy"],
    "chemistry": ["chem", "is", "try"],
    "geography": ["ge", "og", "ra", "phy"],
    "history": ["his", "to", "ry"],
    "physics": ["phys", "ics"],
    "mathematics": ["math", "e", "mat", "ics"],
    "maths": ["m", "aths"],
    "creative": ["cre", "at", "ive"],
    "talented": ["tal", "ent", "ed"],
    "cheerful": ["cheer", "ful"],
    "charming": ["charm", "ing"],
    "positive": ["pos", "i", "tive"],
    "active": ["act", "ive"],
    "concentrate": ["con", "cen", "trate"],
    "pollution": ["pol", "lu", "tion"],
    "recycle": ["re", "cy", "cle"],
    "rubbish": ["rub", "bish"],
    "invitation": ["in", "vi", "ta", "tion"],
    "invitations": ["in", "vi", "ta", "tions"],
    "organise": ["or", "gan", "ise"],
    "organize": ["or", "gan", "ize"],
    "dinner": ["din", "ner"],
    "nurse": ["n", "urse"],
    "clown": ["cl", "own"],
    "beard": ["b", "eard"],
    "blonde": ["bl", "onde"],
    "field": ["f", "ield"],
    "grass": ["gr", "ass"],
    "ground": ["gr", "ound"],
    "straight": ["str", "aight"],
    "smash": ["sm", "ash"],
    "lake": ["l", "ake"],
    "rock": ["r", "ock"],
    "cook": ["c", "ook"],
    "tall": ["t", "all"],
    "thin": ["th", "in"],
    "aunt": ["au", "nt"],
    "short": ["sh", "ort"],
    "photo": ["ph", "o", "to"],
    "photos": ["ph", "o", "tos"],
    "club": ["cl", "ub"],
    "blog": ["bl", "og"],
    "pet": ["p", "et"],
    "fun": ["f", "un"],
    "rest": ["r", "est"],
    "time": ["t", "ime"],
    "good": ["g", "ood"],
    "make": ["m", "ake"],
    "take": ["t", "ake"],
    "keep": ["k", "eep"],
    "write": ["wr", "ite"],
    "collect": ["col", "lect"],
    "hobbies": ["hob", "bies"],
    "armchair": ["arm", "ch", "air"],
    "cooker": ["c", "ook", "er"],
    "bookshop": ["b", "ook", "sh", "op"],
    "reputation": ["re", "pu", "ta", "tion"],
    "six": ["s", "ix"],
    "clock": ["cl", "ock"],
    "half": ["h", "alf"],
    "past": ["p", "ast"],
    "three": ["thr", "ee"],
    "twelve": ["tw", "elve"],
    "seven": ["sev", "en"],
    "ear": ["e", "ar"],
    "fat": ["f", "at"],
    "man": ["m", "an"],
    "dad": ["d", "ad"],
    "cat": ["c", "at"],
    "hat": ["h", "at"],
    "bat": ["b", "at"],
    "bag": ["b", "ag"],
    "pen": ["p", "en"],
    "dog": ["d", "og"],
    "pig": ["p", "ig"],
    "sun": ["s", "un"],
    "bus": ["b", "us"],
    "car": ["c", "ar"],
    "van": ["v", "an"],
    "bed": ["b", "ed"],
    "cup": ["c", "up"],
    "box": ["b", "ox"],
    "fox": ["f", "ox"],
    "boy": ["b", "oy"],
    "toy": ["t", "oy"],
    "day": ["d", "ay"],
    "may": ["m", "ay"],
    "say": ["s", "ay"],
    "way": ["w", "ay"],
    "sea": ["s", "ea"],
    "tea": ["t", "ea"],
}

TRANSFERS_DB = {
    "pl": [("player", "演奏者/玩家"), ("plant", "植物"), ("plan", "计划"), ("plastic", "塑料")],
    "ay": [("day", "白天/天"), ("way", "道路/方式"), ("say", "说"), ("stay", "停留")],
    "in": [("inside", "在里面"), ("invite", "邀请"), ("invent", "发明"), ("income", "收入")],
    "stru": [("structure", "结构"), ("instruct", "指导"), ("construct", "建造"), ("destroy", "破坏")],
    "ment": [("document", "文件"), ("payment", "付款"), ("treatment", "治疗"), ("movement", "运动")],
    "wr": [("write", "写"), ("wrong", "错误的"), ("wrap", "包裹"), ("wrist", "手腕")],
    "ite": [("white", "白色的"), ("kite", "风筝"), ("bite", "咬"), ("polite", "有礼貌的")],
    "bl": [("black", "黑色"), ("blue", "蓝色"), ("blind", "盲的"), ("blanket", "毛毯")],
    "og": [("frog", "青蛙"), ("dog", "小狗"), ("fog", "雾"), ("blog", "博客")],
    "cl": [("clock", "时钟"), ("clean", "干净的"), ("climb", "攀爬"), ("cloud", "云朵")],
    "ub": [("club", "俱乐部"), ("subway", "地铁"), ("rub", "摩擦"), ("tub", "浴缸")],
    "ph": [("photo", "照片"), ("phone", "电话"), ("phrase", "短语"), ("physics", "物理学")],
    "gr": [("green", "绿色"), ("great", "伟大的"), ("grow", "成长"), ("ground", "地面")],
    "ass": [("grass", "草地"), ("class", "班级"), ("glass", "玻璃杯"), ("pass", "通过")],
    "str": [("street", "街道"), ("strong", "强壮的"), ("straight", "直的"), ("stream", "小溪")],
    "aight": [("straight", "笔直的"), ("straightforward", "坦率的")],
    "ield": [("field", "田野/球场"), ("yield", "产出/屈服"), ("shield", "盾牌")],
    "ound": [("ground", "地面"), ("sound", "声音"), ("round", "圆的"), ("found", "发现")],
    "ake": [("cake", "蛋糕"), ("lake", "湖泊"), ("make", "制造"), ("take", "拿取")],
    "all": [("ball", "球"), ("call", "呼叫"), ("hall", "大厅"), ("tall", "高的")],
    "ook": [("book", "书"), ("cook", "做饭"), ("look", "看"), ("hook", "挂钩")],
    "sh": [("ship", "轮船"), ("shop", "商店"), ("short", "短的"), ("shine", "照耀")],
    "ch": [("chair", "椅子"), ("chat", "聊天"), ("child", "孩子"), ("check", "检查")],
    "th": [("think", "思考"), ("three", "三"), ("thank", "感谢"), ("thin", "瘦的/薄的")],
    "br": [("brave", "勇敢的"), ("bread", "面包"), ("brother", "兄弟"), ("brown", "棕色")],
    "ave": [("brave", "勇敢的"), ("save", "拯救/保存"), ("wave", "波浪/挥手"), ("cave", "洞穴")],
    "charm": [("charming", "迷人的"), ("charmed", "着迷的")],
    "ing": [("singing", "唱歌"), ("swimming", "游泳"), ("running", "跑步"), ("morning", "早晨")],
    "ful": [("cheerful", "开朗的"), ("helpful", "有帮助的"), ("beautiful", "美丽的"), ("colorful", "多彩的")],
    "act": [("action", "行动"), ("actor", "演员"), ("active", "活跃的"), ("react", "反应")],
    "ive": [("active", "积极的"), ("creative", "创新的"), ("positive", "乐观的"), ("native", "本土的")],
    "cre": [("create", "创造"), ("creative", "创造力的"), ("creature", "生物")],
    "tion": [("action", "行动"), ("station", "车站"), ("question", "问题"), ("vacation", "假期")],
    "sion": [("mission", "使命"), ("vision", "视力/愿景"), ("decision", "决定"), ("expression", "表达")],
    "pol": [("pollution", "污染"), ("police", "警察"), ("policy", "政策")],
    "re": [("recycle", "回收"), ("return", "返回"), ("reuse", "再利用"), ("repeat", "重复")],
    "cle": [("bicycle", "自行车"), ("circle", "圆圈"), ("motorcycle", "摩托车")],
    "rub": [("rubber", "橡胶"), ("rubbish", "垃圾")],
    "un": [("fun", "乐趣"), ("sun", "太阳"), ("run", "跑步"), ("gun", "玩具枪")],
    "est": [("best", "最好的"), ("rest", "休息"), ("test", "测试"), ("nest", "鸟巢")],
    "eep": [("keep", "保持"), ("sleep", "睡觉"), ("deep", "深的"), ("sheep", "绵羊")],
    "ood": [("good", "好的"), ("food", "食物"), ("wood", "木头"), ("mood", "心情")],
    "ime": [("time", "时间"), ("lime", "青柠"), ("climb", "攀爬")],
    "an": [("man", "男人"), ("can", "可以/罐头"), ("fan", "风扇"), ("pan", "平底锅")],
    "ad": [("dad", "爸爸"), ("bad", "坏的"), ("sad", "伤心的"), ("mad", "生气的")],
    "at": [("cat", "猫"), ("hat", "帽子"), ("fat", "胖的"), ("bat", "球棒/蝙蝠")],
    "et": [("pet", "宠物"), ("net", "网"), ("wet", "湿的"), ("set", "放置")],
    "f": [("fun", "乐趣"), ("fish", "鱼"), ("frog", "青蛙"), ("first", "第一")],
    "p": [("pet", "宠物"), ("pen", "钢笔"), ("park", "公园"), ("play", "玩")],
    "t": [("time", "时间"), ("tea", "茶"), ("tall", "高的"), ("toy", "玩具")],
    "k": [("king", "国王"), ("kite", "风筝"), ("kitchen", "厨房")],
    "b": [("ball", "球"), ("boy", "男孩"), ("book", "书"), ("big", "大的")],
    "c": [("cat", "猫"), ("car", "汽车"), ("cup", "杯子"), ("cool", "酷")],
    "h": [("hat", "帽子"), ("hand", "手"), ("house", "房子"), ("happy", "快乐")],
    "m": [("man", "男人"), ("moon", "月亮"), ("milk", "牛奶"), ("map", "地图")],
    "s": [("sun", "太阳"), ("star", "星星"), ("sea", "大海"), ("song", "歌曲")],
    "w": [("water", "水"), ("wind", "风"), ("world", "世界"), ("warm", "温暖")],
}

def chunk_single_word(w):
    clean = re.sub(r'[^a-zA-Z]', '', w)
    if not clean: return [w]
    if len(clean) <= 2: return [w]
    low = clean.lower()
    if low in MANUAL_CHUNKS:
        return MANUAL_CHUNKS[low]

    m_dbl = re.search(r'([bcdfghjklmnpqrstvwxyz])\1', low)
    if m_dbl and 1 < m_dbl.start() + 1 < len(w) - 1:
        split_idx = m_dbl.start() + 1
        return [w[:split_idx], w[split_idx:]]

    for sfx in sorted(SUFFIXES, key=len, reverse=True):
        if low.endswith(sfx) and len(low) > len(sfx) + 2:
            stem = w[:-len(sfx)]
            stem_chunks = chunk_single_word(stem)
            return stem_chunks + [w[-len(sfx):]]

    for pfx in sorted(PREFIXES, key=len, reverse=True):
        if low.startswith(pfx) and len(low) > len(pfx) + 2:
            rem = w[len(pfx):]
            rem_chunks = chunk_single_word(rem)
            return [w[:len(pfx)]] + rem_chunks

    for o3 in ONSET_3:
        if low.startswith(o3) and len(w) > 3:
            return [w[:3], w[3:]]

    for o2 in ONSET_2:
        if low.startswith(o2) and len(w) > 2:
            return [w[:2], w[2:]]

    if low[0] not in VOWELS:
        if len(low) >= 3 and low[1] in VOWELS:
            v_indices = [i for i, c in enumerate(low) if c in VOWELS]
            if len(v_indices) >= 2 and len(low) >= 5:
                mid = (v_indices[0] + v_indices[1]) // 2 + 1
                return [w[:mid], w[mid:]]
            return [w[:1], w[1:]]

    if low[0] in VOWELS:
        if len(low) >= 4:
            return [w[:2], w[2:]]
        elif len(low) == 3:
            return [w[:1], w[1:]]

    mid = len(w) // 2
    return [w[:mid], w[mid:]]

def refine_blocks(word, current_blocks):
    if len(current_blocks) == 3 and all(len(b) == 1 for b in current_blocks):
        c1, c2, c3 = current_blocks[0], current_blocks[1], current_blocks[2]
        if c1 not in VOWELS and c2 in VOWELS and c3 not in VOWELS:
            return [c1, c2 + c3]

    res = []
    for b in current_blocks:
        b_clean = re.sub(r'[^a-zA-Z0-9]', '', b)
        if not b_clean:
            continue
        low = b_clean.lower()
        if low in MANUAL_CHUNKS:
            res.extend(MANUAL_CHUNKS[low])
        elif len(b_clean) > 2 and (b_clean.lower() == word.lower() or " " in word or len(current_blocks) == 1):
            chunks = chunk_single_word(b_clean)
            res.extend(chunks)
        else:
            res.append(b)

    final = [x for x in res if x]
    return final if final else [word]

def refine_transfers(word, blocks, current_transfers):
    refined = []
    seen = {word.lower()}

    if current_transfers and isinstance(current_transfers, list):
        for t in current_transfers:
            tw = t.get("word", "")
            thl = t.get("hl", "")
            tcn = t.get("cn", "")
            if not tw: continue
            
            if thl in blocks and tw.lower() not in seen:
                seen.add(tw.lower())
                refined.append({"word": tw, "hl": thl, "cn": tcn})
            else:
                matched_b = None
                for b in blocks:
                    if b.lower() in tw.lower():
                        matched_b = b
                        break
                if matched_b and tw.lower() not in seen:
                    seen.add(tw.lower())
                    refined.append({"word": tw, "hl": matched_b, "cn": tcn})

    if len(refined) < 4:
        for b in blocks:
            b_low = b.lower()
            if b_low in TRANSFERS_DB:
                for tw, tcn in TRANSFERS_DB[b_low]:
                    if tw.lower() not in seen and b_low in tw.lower():
                        seen.add(tw.lower())
                        refined.append({"word": tw, "hl": b, "cn": tcn})
                    if len(refined) >= 4: break
            if len(refined) >= 4: break

    if len(refined) < 2:
        for b in sorted(blocks, key=len, reverse=True):
            b_low = b.lower()
            if len(b_low) < 2: continue
            for gw, gcn in GLOBAL_TRANSLATIONS.items():
                if b_low in gw and gw not in seen and len(gw) <= 12 and " " not in gw:
                    seen.add(gw)
                    refined.append({"word": gw, "hl": b, "cn": gcn})
                if len(refined) >= 4: break
            if len(refined) >= 4: break

    return refined[:4]

def refine_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as fp:
        html = fp.read()

    m = re.search(r'const VOCABULARY = (\[[\s\S]*?\]);', html)
    if not m:
        return False, "No VOCABULARY found"

    raw_vocab = m.group(1).strip()
    if re.search(r'^\s*[a-zA-Z_]\w*\s*:', raw_vocab, re.MULTILINE):
        raw_vocab = re.sub(r'([{,]\s*)([a-zA-Z_]\w*)\s*:', r'\1"\2":', raw_vocab)
        raw_vocab = re.sub(r',\s*([}\]])', r'\1', raw_vocab)

    try:
        vocab = json.loads(raw_vocab)
    except Exception as e:
        return False, f"JSON parse error: {e}"

    for item in vocab:
        w = item.get("word", "")
        item["blocks"] = refine_blocks(w, item.get("blocks", []))
        item["transfers"] = refine_transfers(w, item["blocks"], item.get("transfers", []))

    new_vocab_js = f"const VOCABULARY = {json.dumps(vocab, ensure_ascii=False, indent=6)};"
    html = re.sub(r'const VOCABULARY = \[[\s\S]*?\];', lambda _: new_vocab_js, html)

    if 'id="ahaSyncBanner"' not in html:
        banner_html = """      <!-- Aha! 生词本双向打通同步横幅 -->
      <div id="ahaSyncBanner" style="display:none; align-items: center; justify-content: space-between; background: linear-gradient(135deg, rgba(88,204,2,0.12), rgba(28,176,246,0.12)); border: 1.5px solid #58CC02; border-radius: 14px; padding: 8px 12px; margin-bottom: 12px; font-size: 11px; font-weight: 800; color: #1D1D1F;">
        <div style="display: flex; align-items: center; gap: 6px;">
          <span>⚡</span>
          <span>已成功打通并同步来自 <strong>Aha! 生词本</strong> 的 <span id="ahaSyncCount" style="color: #46A302; font-size: 13px;">0</span> 个重点词汇</span>
        </div>
        <button onclick="document.getElementById('ahaSyncBanner').style.display='none'" style="background:none; border:none; color:#888; cursor:pointer; font-size:12px; font-weight:bold;">✕</button>
      </div>"""
        html = re.sub(r'(<header class="learn-header">[\s\S]*?</header>)', r'\1\n' + banner_html, html)

    if 'function syncFromAha()' not in html:
        sync_js = """
    function syncFromAha() {
      try {
        const raw = localStorage.getItem('kron_word_current_unit_payload') || localStorage.getItem('kron_saved_words') || localStorage.getItem('kron:word:shared_vocab');
        if (!raw) return;
        const data = JSON.parse(raw);
        const words = Array.isArray(data) ? data : (data.words || []);
        if (!words || words.length === 0) return;

        const savedMap = new Map();
        words.forEach(w => {
          if (w.word) savedMap.set(w.word.toLowerCase().trim(), w);
        });

        let matched = 0;
        VOCABULARY.forEach(item => {
          const wClean = item.word.toLowerCase().trim();
          const hasDirect = savedMap.has(wClean);
          const hasContained = Array.from(savedMap.keys()).some(k => k && (wClean.includes(k) || k.includes(wClean)));
          if (hasDirect || hasContained) {
            item.isAhaSaved = true;
            matched++;
          }
        });

        words.forEach(w => {
          const wClean = (w.word || '').toLowerCase().trim();
          const exists = VOCABULARY.some(v => {
            const vClean = v.word.toLowerCase().trim();
            return vClean === wClean || vClean.includes(wClean);
          });
          if (!exists && wClean) {
            let blocks = [w.word];
            if (wClean === 'instrument') {
              blocks = ['in', 'stru', 'ment'];
            } else if (wClean === 'play') {
              blocks = ['pl', 'ay'];
            } else if (wClean === 'play an instrument') {
              blocks = ['pl', 'ay', 'an', 'in', 'stru', 'ment'];
            } else {
              const rawParts = w.word.split(/\\s+/).filter(Boolean);
              blocks = rawParts.length > 1 ? rawParts : [w.word];
            }
            VOCABULARY.push({
              word: w.word,
              meaning: w.translation || 'Aha! 重点词汇',
              IPA: w.phonetic || `/${wClean}/`,
              type: w.partOfSpeech || 'saved',
              blocks,
              mindSpark: '你在 Kron English Aha! 学习中亲手收藏的重点单词，快来拼出它吧！',
              rule: 'Aha! 生词本同步词汇',
              ruleDesc: '来自课堂实战提问与高频语境，属于你的专属记忆！',
              transfers: [],
              isAhaSaved: true
            });
            matched++;
          }
        });

        const banner = document.getElementById('ahaSyncBanner');
        const countEl = document.getElementById('ahaSyncCount');
        if (banner && countEl && words.length > 0) {
          countEl.innerText = words.length;
          banner.style.display = 'flex';
        }
      } catch (e) {
        console.warn('Aha sync notice:', e);
      }
    }
"""
        html = re.sub(r'(function initWord\(\)\s*\{)', lambda m: sync_js + '\n    ' + m.group(1), html)
        if 'syncFromAha();' not in html:
            html = re.sub(r'(initWord\(\);)', lambda m: 'syncFromAha();\n    ' + m.group(1), html)

    with open(file_path, "w", encoding="utf-8") as fp:
        fp.write(html)

    return True, "Updated"

def main():
    files = sorted([f for f in os.listdir(WORD_DIR) if f.endswith(".html")])
    for f in files:
        refine_html_file(os.path.join(WORD_DIR, f))
    print(f"Refined {len(files)} files.")

if __name__ == "__main__":
    main()
