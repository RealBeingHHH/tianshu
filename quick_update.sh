#!/bin/bash
# 天枢一键更新 - 自动找到安装位置并拉取最新代码
set -e

# 1. 找到天枢
for dir in \
    ~/.hermes/skills/tianshu4 \
    ~/.hermes/skills/tianshu \
    /opt/tianshu \
    ~/tianshu-opensource \
    ~/tianshu; do
    if [ -d "$dir/.tianshu" ] || [ -f "$dir/reference/seal.py" ]; then
        TIANSHU_DIR="$dir"
        break
    fi
done

# 2. 没找到就 clone
if [ -z "$TIANSHU_DIR" ]; then
    echo "🔍 未找到天枢，正在安装..."
    TIANSHU_DIR=~/tianshu
    git clone https://github.com/RealBeingHHH/tianshu.git "$TIANSHU_DIR"
else
    echo "✅ 找到天枢: $TIANSHU_DIR"
fi

# 3. 更新
cd "$TIANSHU_DIR"
if [ -d .git ]; then
    echo "📥 从 GitHub 拉取..."
    git pull origin main
else
    # 不是 git 目录，从上游同步
    echo "📥 从上游同步..."
    cd /tmp
    git clone --depth 1 https://github.com/RealBeingHHH/tianshu.git _tianshu_tmp 2>/dev/null

    # 检查目标目录是否可写（chattr +i 保护的天枢不可直接覆盖）
    if [ -w "$TIANSHU_DIR/reference" ] 2>/dev/null; then
        cp -r _tianshu_tmp/reference "$TIANSHU_DIR/"
        cp -r _tianshu_tmp/tools "$TIANSHU_DIR/"
        cp _tianshu_tmp/QUICKSTART.md "$TIANSHU_DIR/" 2>/dev/null || true
    else
        echo "⚠️  $TIANSHU_DIR 受 chattr 保护，跳过核心文件覆盖"
        echo "   如需更新: sudo chattr -i $TIANSHU_DIR/.tianshu/* 然后重试"
    fi

    # 文档和仪表盘总是可以更新（不影响封印）
    mkdir -p "$TIANSHU_DIR/dashboards" "$TIANSHU_DIR/dialogues" "$TIANSHU_DIR/docs" 2>/dev/null
    cp _tianshu_tmp/QUICKSTART.md "$TIANSHU_DIR/" 2>/dev/null || true
    cp _tianshu_tmp/QUICKSTART.en.md "$TIANSHU_DIR/" 2>/dev/null || true
    cp _tianshu_tmp/ARCHITECTURE.md "$TIANSHU_DIR/" 2>/dev/null || true
    rm -rf _tianshu_tmp
fi

# 4. 验证
echo ""
echo "═══ 天枢更新完成 ═══"
echo "   目录: $TIANSHU_DIR"

# 验证模块可导入
python3 -c "
import sys; sys.path.insert(0,'$TIANSHU_DIR/reference')
from seal import SealEngine; print('   seal.py: ✅')
from sentinel import Sentinel; print('   sentinel.py: ✅')
" 2>/dev/null || echo "   ⚠️  部分模块导入失败（如已封印部署则正常）"

echo ""
echo "   模拟引擎: python3 $TIANSHU_DIR/tools/simulate_enhanced.py"
echo "   API服务:  python3 $TIANSHU_DIR/reference/api.py"
