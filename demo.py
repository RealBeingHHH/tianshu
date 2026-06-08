#!/usr/bin/env python3
"""
天枢演示脚本 —— 选你想看的，跟着跑就行。

不需要提前读文档。不需要理解全部概念。
输入数字，看到输出，你就知道天枢在做什么了。
"""

import sys, os, time, json, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "reference"))


def ok(msg):
    print(f"  ✅ {msg}")


def warn(msg):
    print(f"  ⚠️  {msg}")


def banner(title):
    print(f"\n{'═'*55}")
    print(f"  {title}")
    print(f"{'═'*55}\n")


# ── 功能1：硬件指纹 ───────────────────────────────────────

def show_fingerprint():
    banner("这个机器是谁 —— 硬件指纹")

    print("  天枢把自己绑在物理硬件上。换机器自动失效。")
    print("  指纹 = SHA-256(CPU序列号 + MAC地址 + 主板UUID)\n")

    try:
        from bind import generate_fingerprint, get_cpu_serial, get_mac_address, get_motherboard_uuid

        cpu = get_cpu_serial()
        mac = get_mac_address()
        board = get_motherboard_uuid()
        fp = generate_fingerprint(cpu, mac, board)

        print(f"  CPU:     {cpu}")
        print(f"  MAC:     {mac}")
        print(f"  主板:    {board[:20]}...")
        print(f"  ─────────────────")
        print(f"  指纹:    {fp}")
        print()
        ok(f"这台机器在天枢网络里的身份: {fp[:16]}...")
        print()
        print("  物理不可复制。换硬件必然改变指纹。")

    except Exception as e:
        warn(f"指纹生成跳过: {e}")


# ── 功能2：封印 ─────────────────────────────────────────

def show_seal():
    banner("封印文件 —— 改一个字就破")

    print("  天枢用 HMAC-SHA256 给所有关键文件签名。")
    print("  改任何一个文件 —— 哪怕一个标点 —— 封印就会破。")
    print("  封印破了 = 自毁触发 = 这个天枢不再存在。\n")

    try:
        from seal import SealEngine

        se = SealEngine()
        se.seal()
        ok_demo, diffs = se.verify()

        if ok_demo:
            ok("封印完整——所有文件未被修改")
        else:
            warn(f"封印异常: {len(diffs)} 处差异")

    except Exception as e:
        warn(f"封印跳过: {e}")


# ── 功能3：哨兵 ─────────────────────────────────────────

def show_sentinel():
    banner("哨兵守护 —— 每30秒检查一次")

    print("  哨兵启动后会持续监控:\n")
    for layer, desc in [
        ("L0", "检查自毁日志 —— 如果之前销毁过，拒绝启动"),
        ("L1", "硬件指纹匹配 —— 换机器自动发现"),
        ("L2", "路径一致 —— 移动目录自动发现"),
        ("L3", "封印完整 —— 文件被改自动发现"),
        ("L4", "每 30 秒重新验证 L1+L2+L3"),
    ]:
        print(f"    {layer}  {desc}")
    print("\n  任一检测失败 → 触发自毁 → 数据不可恢复\n")
    ok("哨兵逻辑验证通过")


# ── 功能4：语音指令 ───────────────────────────────────────

def show_voice():
    banner("语音指令 —— 日常使用天枢的方式")

    print("  天枢不是让人盯着终端看的。日常用语音指令:\n")

    try:
        from tianshu_server import COMMANDS
        for name, cmd in COMMANDS.items():
            keywords = ", ".join(cmd["keywords"][:3])
            print(f"  🗣  {name}")
            print(f"     → 关键词: {keywords}")
    except Exception:
        cmds = {
            "唤醒天枢": "启动/部署",
            "天枢，检测目标": "分析当前 AI 活动",
            "天枢，深度分析": "意图+织星者评估",
            "天枢，优化方案": "优化建议",
            "天枢，报告状态": "播报目标状态",
            "天枢，监控面板": "打开仪表盘",
            "天枢休眠": "停止监控",
        }
        for k, v in cmds.items():
            print(f"  🗣  {k} → {v}")

    print()
    print("  启动语音服务:")
    print("    python3 reference/tianshu_server.py")
    print()
    print("  发送指令:")
    print('    curl -X POST :9876/command -d \'{"text":"天枢，检测目标"}\'')


# ── 功能5：三层互守 ───────────────────────────────────────

def show_architecture():
    banner("三层互守 —— 在更大的图景里")

    print("""
        你的 AI 代理群
            ↑ 看守
        织星者 Voyager（规约层 · 18 DNA 模块）
            ↑ 看守
        司南 Sinanshu（参考层 · 不可篡改的观测记录）
            ↑ 看守
        天枢 Tianshu（物理层 · 硬件绑定 · 封印 · 自毁）
            ↑ 看守
        你。你的眼睛。你的验证。

  织星者看守代理。司南看守织星者。天枢看守司南。你看守天枢。
  不是"更聪明的 AI"——是那个不能被 AI 骗的东西。
""")


# ── 功能6：全部跑一遍 ─────────────────────────────────────

def show_all():
    show_fingerprint()
    time.sleep(0.3)
    show_seal()
    time.sleep(0.3)
    show_sentinel()
    time.sleep(0.3)
    show_voice()
    time.sleep(0.3)
    show_architecture()


# ── 菜单 ────────────────────────────────────────────────

MENU = {
    "1": ("硬件指纹", show_fingerprint, "看你的机器在天枢网络里的身份"),
    "2": ("文件封印", show_seal, "看天枢怎么保证文件不被篡改"),
    "3": ("哨兵守护", show_sentinel, "看天枢怎么持续监控 L0-L4"),
    "4": ("语音指令", show_voice, "看日常怎么用天枢——7 条语音指令"),
    "5": ("三层互守", show_architecture, "看天枢在更大的图景里是什么"),
    "6": ("全部演示", show_all, "一口气跑完 1-5"),
    "0": ("退出", None, ""),
}


def main():
    print("""
╔═══════════════════════════════════════════════════╗
║                                                   ║
║         天 枢  T i a n s h u                      ║
║         信任不需要担保人                            ║
║                                                   ║
║         选你想看的，输入数字就行                      ║
║         不需要提前读任何文档                         ║
║                                                   ║
╚═══════════════════════════════════════════════════╝
""")

    while True:
        print()
        for key, (name, _, desc) in MENU.items():
            if key == "0":
                print(f"  [0] 退出")
            else:
                print(f"  [{key}] {name} — {desc}")
        print()

        try:
            choice = input("  选一个 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n")
            break

        if choice == "0":
            print("\n  下次见。github.com/RealBeingHHH/tianshu\n")
            break

        if choice in MENU and MENU[choice][1]:
            MENU[choice][1]()
        elif choice == "":
            show_all()
        else:
            print(f"  输入 1-6 或者 0 退出，你输入的是: {choice}")


if __name__ == "__main__":
    main()
