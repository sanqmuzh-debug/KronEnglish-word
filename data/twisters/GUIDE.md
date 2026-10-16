# Kron Word 绕口令写作规范（写批次用）

每个词或词块写一条：英文绕口令 tw、中文 twc、脑洞 hint、梗图编号 meme、Nano Banana 2.1 提示词 prompt。
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

## 梗图 meme（只借构图和表情）
m01 this is fine：周围全乱，Kron 淡定
m02 distracted boyfriend：Kron 走着回头盯别的，身边的生气
m03 side-eye：斜眼瞅旁边
m04 shocked face：瞪眼张嘴大特写
m05 two buttons：两个选择前急出冷汗
m06 reject vs approve 两格：对 A 嫌弃、对 B 满意
m07 superhero landing：慢动作单膝跪地
m08 all according to plan：手指交叉阴险微笑
m09 leaning back in shock：被吓得往后一仰
m10 confused stare：问号脸
m11 totally drained：躺平、灵魂出窍
m12 everyone staring：全场眼睛盯着 Kron
m13 proud hands on hips：抬下巴叉腰
m14 expectation vs reality 两格
m15 cool guys don't look at explosions：酷酷走来，身后大乱
m16 tables turned：Kron 整别人反被整
同一批 20 条里尽量分散，任一编号最多用 3 次。

## 提示词 prompt（英文，固定 7 行，用 \n 分隔）
1. 固定一行：Using the attached character sheet, keep Kron exactly as designed: same proportions, colours, face and quills, as a 25 cm plush toy.
2. 动作：把绕口令照字面演出来，谁在做什么，Kron 的表情。
3. The composition follows the "<梗名>" meme: <这张怎么摆>.
4. The scene is <在哪里，几件关键道具>.
5. 镜头：Shot ... with a NN mm lens, 谁清楚谁虚, depth of field.
6. 光和色：布光方式 + colour grade。
7. 固定开头：A real-photography 4:3 landscape film still, photoreal <材质>, a clean frame with no lettering.
场景、镜头、光每条都不一样，跟着绕口令走。Kron 在画面中间三分之一。画面里需要纸、屏幕、招牌时写成 blank。

## 示例

```json
{
 "w": "pencil",
 "meme": "m16",
 "tw": "Kron's pencil pens a penguin, and the penguin pencils a penny on Kron.",
 "twc": "Kron 的铅笔画了只企鹅，企鹅反手在 Kron 脸上画了枚硬币。",
 "hint": "画企鹅的代价是被企鹅画。",
 "prompt": "Using the attached character sheet, keep Kron exactly as designed: same proportions, colours, face and quills, as a 25 cm plush toy.\nKron holds a pencil almost as tall as himself and has just finished sketching a penguin on a large sheet of paper, but the real penguin standing next to him has grabbed a second pencil and is calmly drawing a big round penny on Kron's cheek while Kron freezes, eyes wide.\nThe composition follows the \"tables turned\" meme: the trickster gets tricked, Kron in the middle, the smug penguin leaning in from the right.\nThe scene is a snowy Antarctic shore with an easel stuck in the ice and a few curious penguins in the background.\nShot at eye level with a 50 mm lens, Kron and the penguin sharp, the colony softly blurred, shallow depth of field.\nCold overcast daylight with a soft blue cast, bright snow bouncing light onto Kron's face, crisp documentary colour grade.\nA real-photography 4:3 landscape film still, photoreal fur and feathers, a clean frame with blank paper and no lettering."
}
```

```json
{
 "w": "take part in",
 "meme": "m15",
 "tw": "Kron takes part in the parrot party and takes apart the party cart.",
 "twc": "Kron 去参加鹦鹉派对，顺手把派对推车拆了。",
 "hint": "参加派对，拆了派对。",
 "prompt": "Using the attached character sheet, keep Kron exactly as designed: same proportions, colours, face and quills, as a 25 cm plush toy.\nKron walks calmly toward the camera wearing a party hat and carrying a wheel and a screwdriver, while behind him the party snack cart collapses into pieces and a flock of colourful parrots flap and squawk in panic.\nThe composition follows the \"cool guys don't look at explosions\" meme: Kron unbothered in front, chaos behind.\nThe scene is a garden party with paper lanterns, balloons and confetti in the air.\nShot at Kron's eye level with a 50 mm lens, Kron sharp, the chaos behind slightly blurred with motion.\nEarly evening light with string lights glowing and confetti backlit, rich festive colour grade.\nA real-photography 4:3 landscape film still, photoreal feathers and props, a clean frame with no lettering."
}
```

```json
{
 "w": "sustainable",
 "meme": "m01",
 "tw": "Kron sustains a stable table of tins on one tiny toe.",
 "twc": "Kron 用一根小脚趾稳稳托住一张堆满罐头的桌子。",
 "hint": "撑得住，才叫可持续。",
 "prompt": "Using the attached character sheet, keep Kron exactly as designed: same proportions, colours, face and quills, as a 25 cm plush toy.\nKron stands on one foot and balances a small table piled high with recycled tin cans on the tip of his other raised toe, wobbling slightly but keeping a calm, confident smile.\nThe composition follows the \"this is fine\" meme: an impossible balance held with total calm.\nThe scene is a bright recycling yard with neat bins and stacked cans.\nShot at eye level with a 35 mm lens, Kron and the tower of tins sharp, the yard soft behind.\nClean morning daylight with bright reflections on the tins, fresh green colour grade.\nA real-photography 4:3 landscape film still, photoreal metal and plush fur, a clean frame with label-free cans and no lettering."
}
```

## 词头有问题时
个别词头带 OCR 残留（如 complexity n、2ussian、1 / one）：w 原样照抄不改，按显然的本意写（complexity、Russian、one），并在 notes-<段号>.txt 里记一行「批号 词头 → 本意」。

## 输出
每批一个文件 data/twisters/NNN.json（对应 todo-NNN.json），JSON 数组，顺序同 todo，每项 {"w","meme","tw","twc","hint","prompt"}，w 原样照抄 todo。
写完自查：tw 里含目标词、词数 8–16、twc ≤30 字、hint ≤15 字、prompt 恰好 7 行且首行末行是固定句、meme 合法。
