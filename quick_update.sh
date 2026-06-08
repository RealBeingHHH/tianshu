#!/bin/bash
# 天枢一键更新 - 自动找到安装位置并拉取最新代码

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
    git pull origin main
else
    # 不是 git 目录，重新下载
    cd /tmp
    git clone https://github.com/RealBeingHHH/tianshu.git _tianshu_tmp
    cp -r _tianshu_tmp/reference "$TIANSHU_DIR/"
    cp -r _tianshu_tmp/tools "$TIANSHU_DIR/"
    cp _tianshu_tmp/QUICKSTART.md "$TIANSHU_DIR/" 2>/dev/null
    rm -rf _tianshu_tmp
fi

# 4. 验证
echo ""
echo "═══ 天枢更新完成 ═══"
echo "   目录: $TIANSHU_DIR"
python3 "$TIANSHU_DIR/reference/sentinel.py" --version 2>/dev/null || \
    python3 -c "import sys; sys.path.insert(0,'$TIANSHU_DIR/reference'); from seal import SealEngine; print('   seal.py: ✅'); from sentinel import Sentinel; print('   sentinel.py: ✅')" 2>/dev/null
echo ""
echo "   语音服务: python3 $TIANSHU_DIR/reference/tianshu_server.py"
echo "   --port 9876"
