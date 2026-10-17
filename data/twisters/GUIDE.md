# Kron Word 绕口令写作规范（写批次用）

每个词或词块写一条：英文绕口令 tw、中文 twc、脑洞 hint。图片提示词不在这里写（由 Antigravity 负责）。
标准原文：https://claude.ai/code/artifact/1ea3b37c-5770-4fb8-afb5-9986864e7053

## 绕口令 tw
- 一句英文，8–16 个词。目标词原样出现一次（词块整块出现，大小写可随句首）。
- 重读音节在别的词里至少再响两次（整句至少三次）；多音节词每个音节都尽量在句子里再响一次（grandfather：grand / far, farm / rather）。音节参考 syl 字段。
- 同一批里意思相近的词（grandma / grandpa / grandfather）要写出完全不同的句子和场景，不共用押韵词。
- 主角永远是 Kron（可写 Kron / Kronny / Ron 以配合发音），画里都是 Kron。配角可以是人、动物或东西。
- 用词不超过目标词的级别：小学词的句子只用小学常见词。
- 必须画得出来：一个画面、一个动作、一个荒诞点，好笑，不写抽象话。
- 句型/长句子（本身就是一句话的条目）：整句原样用，前后加短短一截押韵的内容，总长不超过 16 词，例：Kron asks a wet white feather, "What's the weather like today?"
- 不写 hedgehog / 刺猬。

## 中文 twc
直译绕口令，留住笑点，30 字以内。

## 脑洞 hint
一句中文，15 字以内，点破图里最好笑的那一下并跟词义挂钩。不重复翻译，不讲道理，不堆感叹号。

## 示例

```json
{
 "w": "pencil",
 "tw": "Kron's pencil pens a penguin, and the penguin pencils a penny on Kron.",
 "twc": "Kron 的铅笔画了只企鹅，企鹅反手在 Kron 脸上画了枚硬币。",
 "hint": "画企鹅的代价是被企鹅画。"
}
```

```json
{
 "w": "take part in",
 "tw": "Kron takes part in the parrot party and takes apart the party cart.",
 "twc": "Kron 去参加鹦鹉派对，顺手把派对推车拆了。",
 "hint": "参加派对，拆了派对。"
}
```

```json
{
 "w": "sustainable",
 "tw": "Kron sustains a stable table of tins on one tiny toe.",
 "twc": "Kron 用一根小脚趾稳稳托住一张堆满罐头的桌子。",
 "hint": "撑得住，才叫可持续。"
}
```

## 词头有问题时
个别词头带 OCR 残留（如 complexity n、2ussian、1 / one）：w 原样照抄不改，按显然的本意写（complexity、Russian、one），在这一条里加 "say": "本意"（check.py 会用它检查），并在 notes-<段号>.txt 里记一行「批号 词头 → 本意」。带省略号的词块（bring... under control）照常写成完整句子，check.py 会分段检查，不用加 say。

## 输出
每批一个文件 data/twisters/NNN.json（对应 todo-NNN.json），JSON 数组，顺序同 todo，每项 {"w","tw","twc","hint"}，w 原样照抄 todo。
写完自查：tw 里含目标词、词数 8–16、twc ≤30 字、hint ≤15 字。
