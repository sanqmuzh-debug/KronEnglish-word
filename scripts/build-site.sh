#!/bin/bash
# 把网站要发布的文件拷进 dist/：首页、manifest、data/、demo/、public/（不拷脚本、server.py、文档）。
# 发布：合并到 main 后 GitHub Actions 自动发布（.github/workflows/deploy.yml）；手动：./scripts/build-site.sh && npx wrangler pages deploy dist --project-name kronword --branch main
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist
cp index.html console.html manifest.json favicon.svg favicon.ico apple-touch-icon.png dist/
for d in data demo public; do rsync -a --exclude '*.py' --exclude '__pycache__' "$d" dist/; done
# 书架就是网站首页：kronword.pages.dev/ 直接打开 Kron Word（资源仍在 demo/ 下），旧地址 /demo/kron-word 跳回首页。
sed 's#<head><meta charset="utf-8">#<head><meta charset="utf-8"><base href="/demo/">#' demo/kron-word.html > dist/index.html
grep -q '<base href="/demo/">' dist/index.html || { echo "首页没生成好"; exit 1; }
printf '%s\n' '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=/"><script>location.replace("/"+location.hash)</script>' > dist/demo/kron-word.html
# 网站小图标：Kron English logo（黑白自适应 favicon.svg，浅色 #1D1D1F / 深色 #FFFFFF），统一注入所有页面。
ICON='<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="alternate icon" href="/favicon.ico"><link rel="apple-touch-icon" href="/apple-touch-icon.png">'
find dist -name '*.html' -exec grep -l '</head>' {} + | while read -r f; do sed -i.bak "s#</head>#$ICON</head>#" "$f" && rm "$f.bak"; done
grep -q 'rel="icon" href="/favicon.svg"' dist/index.html || { echo "小图标没注入"; exit 1; }
echo "dist: $(find dist -type f | wc -l | tr -d ' ') 个文件"
