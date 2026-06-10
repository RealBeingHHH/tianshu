#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  天枢 Tianshu — 一键安装
#  用法: bash install_tianshu.sh
# ═══════════════════════════════════════════════════════════
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
say() { echo -e "${GREEN}[天枢]${NC} $1"; }
warn() { echo -e "${YELLOW}[警告]${NC} $1"; }
err() { echo -e "${RED}[错误]${NC} $1"; exit 1; }

echo ""
echo "════════════════════════════════════════"
echo "  天枢 Tianshu v6.0 — 一键安装"
echo "  信任的物理锚 · 不可篡改的验证基础设施"
echo "════════════════════════════════════════"
echo ""

# ── 1. 检查 Python ──
say "检查 Python..."
python3 --version 2>/dev/null || err "需要 Python 3.9+。请先安装: apt install python3"
PYVER=$(python3 -c 'import sys; print(sys.version_info.minor)')
[ "$PYVER" -ge 9 ] || err "需要 Python 3.9+，当前版本过低"

# ── 2. 获取代码 ──
INSTALL_DIR="${1:-$HOME/tianshu}"
say "安装目录: $INSTALL_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
    say "已有天枢目录，更新中..."
    cd "$INSTALL_DIR"
    git pull origin main 2>/dev/null || warn "git pull 失败，使用本地版本"
else
    say "克隆天枢仓库..."
    git clone https://github.com/RealBeingHHH/tianshu.git "$INSTALL_DIR" 2>/dev/null || \
    git clone git@github.com:RealBeingHHH/tianshu.git "$INSTALL_DIR" 2>/dev/null || \
    err "无法克隆仓库。请检查网络，或手动下载: https://github.com/RealBeingHHH/tianshu"
fi

cd "$INSTALL_DIR"

# ── 3. 生成硬件指纹 ──
say "生成硬件指纹..."
python3 reference/bind.py --save 2>/dev/null || {
    warn "硬件指纹生成失败（可能是 WSL 环境）。继续安装..."
    mkdir -p .tianshu
    python3 -c "
import hashlib, uuid, json, os
fp = hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()[:16]
os.makedirs('.tianshu', exist_ok=True)
json.dump({'fingerprint': fp, 'bound': True}, open('.tianshu/trust_root.json','w'))
print(f'  指纹: {fp}')
"
}

# ── 4. 创建封印 ──
say "创建文件封印..."
python3 reference/seal.py seal 2>/dev/null || warn "封印创建失败，可稍后手动执行: python3 reference/seal.py seal"

# ── 5. 安装依赖（可选） ──
say "检查依赖..."
python3 -c "import akshare" 2>/dev/null || {
    warn "akshare 未安装（模拟引擎需要）。安装中..."
    pip install akshare -q 2>/dev/null || warn "akshare 安装失败（不影响核心功能）"
}

# ── 6. 启动哨兵 ──
say ""
echo "════════════════════════════════════════"
echo "  安装完成！"
echo "════════════════════════════════════════"
echo ""
echo "  目录: $INSTALL_DIR"
echo "  指纹: $(python3 -c "import json; d=json.load(open('.tianshu/trust_root.json')); print(d.get('fingerprint','?'))" 2>/dev/null || echo '?')"
echo ""
echo "  启动天枢哨兵:"
echo "    cd $INSTALL_DIR && python3 reference/sentinel.py"
echo ""
echo "  启动后访问:"
echo "    curl http://localhost:9000/status"
echo ""
echo "  完整文档:"
echo "    cat $INSTALL_DIR/QUICKSTART.md"
echo ""

# ── 询问是否立即启动 ──
read -p "  是否立即启动天枢哨兵？[Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [ -z "$REPLY" ]; then
    say "启动天枢哨兵..."
    python3 reference/sentinel.py &
    sleep 2
    curl -s http://localhost:9000/status 2>/dev/null | python3 -m json.tool 2>/dev/null || \
        echo "  哨兵启动中，稍后访问 http://localhost:9000/status"
fi
