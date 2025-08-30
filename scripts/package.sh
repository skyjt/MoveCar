#!/usr/bin/env bash
set -euo pipefail

# 打包脚本（生成可分发压缩包）
# 使用方式：
#   1) 默认：./scripts/package.sh
#      产物：dist/MoveCar-<YYYYMMDD-HHMMSS>-<gitrev>.tar.gz
#   2) 指定版本：./scripts/package.sh v1.0.0  或  PKG_VERSION=v1.0.0 ./scripts/package.sh
#      产物：dist/MoveCar-v1.0.0.tar.gz
# 说明：
# - 默认输出 tar.gz 到 dist/ 目录；
# - 自动排除 .git/.venv/__pycache__/data/uploads/tests/docs 等仅本地或非运行时必需内容；
# - 用于发布 Release 前的快速打包。

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"

# 解析版本名（优先参数，其次环境变量）
VERSION="${1:-${PKG_VERSION:-}}"
TS="$(date +%Y%m%d-%H%M%S)"
REV="$(git -C "$ROOT_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)"

if [[ -n "$VERSION" ]]; then
  NAME="MoveCar-$VERSION"
else
  NAME="MoveCar-$TS-$REV"
fi

mkdir -p "$DIST_DIR"

# 临时打包目录
PKG_DIR="$(mktemp -d)"/"$NAME"
mkdir -p "$PKG_DIR"

# 需要复制的顶层条目（最小运行时 + 文档）
INCLUDE=(
  "app" "requirements.txt" "docker-compose.yml" ".env.example" "README.md" "readme_zh.md" "docs" "AGENTS.md"
)

for p in "${INCLUDE[@]}"; do
  if [ -e "$ROOT_DIR/$p" ]; then
    rsync -a --exclude "__pycache__" --exclude ".pytest_cache" --exclude ".mypy_cache" \
      "$ROOT_DIR/$p" "$PKG_DIR/"
  fi
done

# 复制辅助文件
cp -f "$ROOT_DIR/.gitignore" "$PKG_DIR/.gitignore" 2>/dev/null || true
cp -f "$ROOT_DIR/.dockerignore" "$PKG_DIR/.dockerignore" 2>/dev/null || true

# 删除运行时不需要的目录
rm -rf "$PKG_DIR/app/uploads" "$PKG_DIR/data" 2>/dev/null || true

ARCHIVE="$DIST_DIR/$NAME.tar.gz"
tar -C "$(dirname "$PKG_DIR")" -czf "$ARCHIVE" "$NAME"

echo "打包完成: $ARCHIVE"
