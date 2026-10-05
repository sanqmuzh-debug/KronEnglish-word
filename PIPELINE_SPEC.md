# Kron Word 全拆分自然拼读流水线工程规范 (PIPELINE_SPEC)

本文档规范 `KronEnglish-word` 架构下的全拆分自然拼读、音节切分、举一反三同构咬合与双向同步标准。

---

## 1. 全拆分黄金法则 (Total Phonics & Morphemes Chunking)

### 1.1 核心戒律：禁止整词保留
除 1~2 字母功能虚词（如 `a`, `an`, `in`, `on`, `to`, `is`, `be`, `do`, `he`, `me`, `we`, `up`）外，**任何大于 2 字母的单词严禁作为单个积木块输出**。

### 1.2 单音节词拆解原则
采用 **首音连缀 (Onset) + 韵尾元音族 (Rime)** 结构：
- **辅音连缀 (Blends) / 二合字母 (Digraphs)** 作为独立首音：
  - `pl-` (`play` ➔ `pl` + `ay`)
  - `gr-` (`grass` ➔ `gr` + `ass`)
  - `str-` (`straight` ➔ `str` + `aight`)
  - `f-` (`field` ➔ `f` + `ield`)
  - `b-` (`book` ➔ `b` + `ook`)
  - `sh-` (`shop` ➔ `sh` + `op`)
  - `cl-` (`club` ➔ `cl` + `ub`)
  - `bl-` (`blog` ➔ `bl` + `og`)
  - `wr-` (`write` ➔ `wr` + `ite`)
  - `k-` (`keep` ➔ `k` + `eep`)
  - `t-` (`take` ➔ `t` + `ake`, `time` ➔ `t` + `ime`)
  - `h-` (`have` ➔ `h` + `ave`, `half` ➔ `h` + `alf`)

### 1.3 多音节词拆解原则
采用 **前缀 (Prefix) + 词根 (Root) + 后缀 (Suffix)** 或自然音节：
- `instrument` ➔ `in` (前缀) + `stru` (词根) + `ment` (名词后缀)
- `creative` ➔ `cre` + `at` + `ive` (形容词后缀)
- `cheerful` ➔ `cheer` + `ful` (形容词后缀)
- `charming` ➔ `charm` + `ing` (分词后缀)
- `traditional` ➔ `tra` + `di` + `tion` + `al`
- `pollution` ➔ `pol` + `lu` + `tion`
- `recycle` ➔ `re` (前缀) + `cy` + `cle`
- `rubbish` ➔ `rub` + `bish`
- `archaeologist` ➔ `ar` + `chae` + `ol` + `o` + `gist`

### 1.4 短语全拆分
短语中的每一个独立单词均按照上述规则解构，积木托盘中仅包含纯粹发音积木块，连接后通过无缝发音引擎拼读。

---

## 2. 100% 举一反三同构咬合 (Homomorphism)

每个词汇条目均需具备 2~4 个 `transfers` 拓展项目：
```json
{
  "word": "player",
  "hl": "pl",
  "cn": "演奏者/玩家"
}
```
**铁律**：
- `hl` 的值必须完全等同于 `blocks` 数组中的某一个积木。
- `word` 的拼写必须包含子串 `hl`。
- 学生拼完上方积木后，高亮部分与上方积木产生视觉同构呼应。

---

## 3. Aha! 生词本双向联动规范

1. **Storage 键名**：
   - 主载荷：`kron_word_current_unit_payload`
   - 共享词表：`kron:word:shared_vocab` / `kron_saved_words`
2. **广播频道**：
   - `new BroadcastChannel('kron_ecosystem_bridge')`
   - 事件：`KRON_WORD_IMPORT`
3. **视觉反馈**：
   - 匹配命中的词汇在右上角标记 `⭐ 生词本重点` 金色勋章。
   - 顶部展现联动同步绿光横幅，统计已导入的重点词汇数量。
