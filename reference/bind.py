#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Copyright (c) 2026 天枢 Tianshu · 定倾 Dingqing（玄鉴 Xuanjian）
"""
bind.py — 天枢硬件指纹绑定（参考实现）。

生成 CPU+MAC+UUID 组合哈希作为主机指纹。
此参考实现展示算法——实际部署需替换为生产环境的指纹生成逻辑。

用法:
    python3 bind.py                    # 生成并显示主机指纹
    python3 bind.py --save             # 生成并保存到 .tianshu/trust_root.json
    python3 bind.py --verify           # 验证当前硬件与存储指纹匹配

原理:
    指纹 = SHA-256(CPU序列号 + MAC地址 + 主板UUID)
    物理不可复制 —— 换硬件必然改变指纹。
"""

import sys, os, json, hashlib, subprocess, platform, uuid


def get_cpu_serial() -> str:
    """获取 CPU 序列号。"""
    try:
        if sys.platform == "linux":
            r = subprocess.run(
                ["dmidecode", "-t", "processor"],
                capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.split("\n"):
                if "ID:" in line:
                    return line.split("ID:")[1].strip()
        elif sys.platform == "win32":
            r = subprocess.run(
                ["wmic", "cpu", "get", "ProcessorId"],
                capture_output=True, text=True, timeout=5
            )
            lines = r.stdout.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
    except Exception:
        pass
    return "CPU_UNKNOWN"


def get_mac_address() -> str:
    """获取第一个物理网卡 MAC 地址。"""
    try:
        mac = uuid.getnode()
        return ":".join(f"{(mac >> i) & 0xff:02x}" for i in range(40, -1, -8))
    except Exception:
        return "MAC_UNKNOWN"


def get_motherboard_uuid() -> str:
    """获取主板 UUID。"""
    try:
        if sys.platform == "linux":
            r = subprocess.run(
                ["dmidecode", "-t", "system"],
                capture_output=True, text=True, timeout=5
            )
            for line in r.stdout.split("\n"):
                if "UUID:" in line:
                    return line.split("UUID:")[1].strip()
    except Exception:
        pass
    return "UUID_UNKNOWN"


def generate_fingerprint(cpu: str, mac: str, board: str) -> str:
    """组合硬件信息生成指纹。"""
    combined = f"{cpu}|{mac}|{board}"
    return hashlib.sha256(combined.encode()).hexdigest()[:32]


def main():
    import argparse
    p = argparse.ArgumentParser(description="天枢硬件指纹绑定")
    p.add_argument("--save", action="store_true", help="保存到 trust_root.json")
    p.add_argument("--verify", action="store_true", help="验证与存储指纹匹配")
    args = p.parse_args()

    # 读取硬件信息
    cpu = get_cpu_serial()
    mac = get_mac_address()
    board = get_motherboard_uuid()
    fp = generate_fingerprint(cpu, mac, board)

    print(f"CPU:     {cpu}")
    print(f"MAC:     {mac}")
    print(f"Board:   {board[:16]}...")
    print(f"指纹:    {fp}")

    base = os.path.dirname(os.path.abspath(__file__))
    trust_path = os.path.join(base, ".tianshu", "trust_root.json")

    if args.save:
        os.makedirs(os.path.dirname(trust_path), exist_ok=True)
        trust_data = {
            "fingerprint": fp,
            "hardware": {
                "cpu": cpu,
                "mac": mac,
                "motherboard": board[:16],
            },
            "bound_at_iso": __import__("datetime").datetime.now().isoformat(),
        }
        with open(trust_path, "w") as f:
            json.dump(trust_data, f, indent=2)
        print(f"\n✅ 已保存到 {trust_path}")

        # 标记绑定
        bound_path = os.path.join(base, ".tianshu", ".bound")
        with open(bound_path, "w") as f:
            json.dump({"fingerprint": fp, "timestamp": trust_data["bound_at_iso"]}, f)
        print(f"✅ 绑定标记: {bound_path}")

    if args.verify:
        if not os.path.exists(trust_path):
            print("\n❌ trust_root.json 不存在，请先 --save")
            sys.exit(1)
        with open(trust_path) as f:
            stored = json.load(f)
        if stored.get("fingerprint") == fp:
            print(f"\n✅ 指纹匹配: {fp}")
        else:
            print(f"\n❌ 不匹配!")
            print(f"   存储: {stored.get('fingerprint')}")
            print(f"   当前: {fp}")


if __name__ == "__main__":
    main()
