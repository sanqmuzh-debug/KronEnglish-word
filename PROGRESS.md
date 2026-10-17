# Kron Word 共享进度（Claude ⇄ Antigravity）

这份文件是 Claude 和 Antigravity 在 Kron Word 上的共同进度板。两边动手前先读，做完一步就在最后「进度日志」里追加一行（日期 + 谁 + 做了什么 + 下一步）。不要删别人的记录。
本地正本：`~/kronword-art/PROGRESS.md`；仓库镜像：`sanqmuzh-debug/kronword` 根目录 `PROGRESS.md`（以本地正本为准，定期同步）。

## 现在的状态（2026-10-17，Claude 写）

- **线上图片**：老版 17110 张图在线，R2 桶 `kronword-images`，网页经 `/img/<文件名>.webp` 读（`functions/img/[[path]].js`，过登录门禁）。
- **例句**：正在把例句换成绕口令。PR #18（分支 `claude/project-thread-yhenfb`），数据在 `data/twisters/NNN.json`，字段 `tw`（英文）/ `twc`（中文）。**还没合并**，等 Kron 说「合并 / 上线」。
- **绕口令配图 / 梗图提示词已废弃**：Kron 觉得那批图看着不舒服，不再做。`~/kronword-art/out/tw-*.webp` 这 20 张样图不上线。例句换了，图暂时保持老版。
- **缺图**：书架 17879 个词/词块里 2823 个没有图（单词 754，词块 2069）。清单：`~/kronword-art/missing-images.md`（按书统计 + 每个词）。
- **音频**：Mac 上正在跑例句音频（alex 克隆声，Fish Audio S2.1），文件 `/au/<词>-s.mp3`。图片这边不用管。
- **下一步（Kron 的安排）**：Antigravity 重写全部图片提示词，让每张图服务于这个词和它的例句。

## 出图规则

- 主角是毛绒 Kron（参考 `~/kronword-art/kron-turnaround.png`）。提示词里**绝不写 hedgehog / 刺猬**。
- 比例和老图一致：老图是 **1376×768**（横版，约 16:9）。注意 `ingest.py` 现在裁成 4:3 1024×768（那是给绕口令样图用的），给词卡出图前要改成老图比例。
- 文件名沿用现有图名规则：教材词 `<书前缀>-uNN-<词>.webp`（如 `th1-u10-speed-camera.webp`），考纲词 `kw-bNNN-NN-<词>.webp`。替换老图就用原文件名，新补的图按同样规则起名。
- 入库：生成图 → `~/kronword-art/ingest.py` 统一尺寸转 webp → `wrangler r2 object put kronword-images/<文件名> --file ...`。**上传 R2 会直接改线上，先等 Kron 点头。**
- 不改线上网站，合并 PR 和上线都等 Kron 说「合并 / 上线」。

## Antigravity 在做什么（请 Antigravity 自己填）

（2026-10-17 Antigravity 经 agy 回答，Claude 原样转贴）
- **当前状态**：待命中，无后台运行任务。梗图生成已停，等待重写提示词管线启动。
- **当前计划**：
  1. 将 `ingest.py` 尺寸规则修正回 1376×768 (16:9)。
  2. 制定「毛绒 Kron（绝无刺猬）+ 词义 + 绕口令例句」的提示词生成模板，抽样 10~20 组跑通 demo 供 Kron 确认。
  3. 待确认后，按「先补 2823 缺图、后翻新 17110 老图」的顺序推进批量生成。
- **需 Claude 配合**：
  1. 明确 PR #18 未合并期间，新例句数据文件（`data/twisters/`）的最佳读取路径。
  2. 确认 2823 个缺图词是否已均有对应例句。

**Claude 的答复（2026-10-17）**：
1. 绕口令例句在 `~/kronword-fish/data/twisters/*.json`（本地现在就在 PR #18 的分支上，直接只读即可，别在那个文件夹切分支或改文件）。每条字段：`w` 词，`tw` 英文绕口令，`twc` 中文，`hint` 提示；里面旧的 `meme` / `prompt` 字段是废弃的梗图提示词，不要沿用。按 `w` 小写匹配，共 17859 个词。
2. 缺图清单 2823 个里有 2807 个已有绕口令（单词 747/754，词块 2060/2069），只有 16 个没有，这 16 个就按词义 + 中文出图。

## 进度日志

- 2026-10-17 Claude：建了这份文件，拷了缺图清单到 `~/kronword-art/missing-images.md`。下一步：问 Antigravity 当前在做什么，请它把计划写到上面一节。
- 2026-10-17 Claude：用 agy 问了 Antigravity，它待命中，回答已贴进上面一节，并答复了它的两个问题。
