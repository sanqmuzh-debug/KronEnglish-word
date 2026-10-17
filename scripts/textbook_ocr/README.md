国内教材词表怎么来的（结果在 data/textbooks/，书由 scripts/import_textbooks.py 生成）：

1. Kron 的 Mac 上 ~/kronword-wordlists：pick.py 从智慧教育平台目录挑每册最新版（人教 PEP / 北师大 / 外研 / 译林 / 沪教，101 册），
   fetch.py 下载每册最后 40 页图片并用 macOS Vision OCR，parse_book.py 按词汇表版式切成单元和词条，covers.py 取第 1 页做封面。
2. 这里的 clean.py（释义续行、词性、音标残片、识别错字）→ stage2.py（人名地名、大小写、中文释义、去重）；
   manual.py 是人工核对过的改动。高中人教/北师大/外研/译林拿 cpsenglish 的文字版词表交叉核对。
