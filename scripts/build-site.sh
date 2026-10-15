#!/bin/bash
# 把网站要发布的文件拷进 dist/：首页、manifest、data/、demo/、public/（不拷脚本、server.py、文档）。
# 发布：合并到 main 后 GitHub Actions 自动发布（.github/workflows/deploy.yml）；手动：./scripts/build-site.sh && npx wrangler pages deploy dist --project-name kronword --branch main
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist
cp index.html console.html manifest.json dist/
for d in data demo public; do rsync -a --exclude '*.py' --exclude '__pycache__' "$d" dist/; done
echo "dist: $(find dist -type f | wc -l | tr -d ' ') 个文件"
