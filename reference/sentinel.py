#!/usr/bin/env python3
"""
sentinel.py — 守护进程。启动验证 + 持续监控。

三重检测:
  L1 硬件: 指纹匹配 → 载体未变
  L2 路径: 挂载点匹配 → 未移动
  L3 完整性: seal验证 → 文件未改

任一失败 → 触发 self_destruct
"""
import sys, os, json, time, threading
from pathlib import Path

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

CHECK_INTERVAL = 30  


class Sentinel:
    """守护进程——启动时验证，运行时持续监控。"""

    def __init__(self):
        self.bound = os.path.exists(os.path.join(BASE, ".tianshu", ".bound"))
        self.checks_passed = 0
        self.checks_failed = 0
        self.running = False

    def startup_verify(self) -> bool:
        """启动时完整验证。三重检测全部通过才放行。"""
        print("🛡 天枢 v3.5 · 守护验证")
        print("═" * 40)

        # v3.5: 自毁检查
        destruct_log = os.path.join(BASE, ".tianshu", "destruction.log")
        if os.path.exists(destruct_log):
            print("  ⛔ 天枢已自毁。destruction.log 存在。拒绝启动。")
            sys.exit(1)

        print("[L1] 载体验证...")
        try:
            from bind import verify_binding
            result = verify_binding()
            if not result["match"]:
                print(f"  ❌ 载体不匹配: {result.get('reason', 'unknown')}")
                print(f"     存储指纹: {result.get('stored_fp', '?')}")
                print(f"     当前指纹: {result.get('current_fp', '?')}")
                self._trigger_protection("HARDWARE_MISMATCH", result)
                return False
            print(f"  ✅ 载体匹配: {result['stored_fp']}")
        except ImportError:
            pass
        except Exception as e:
            self._trigger_protection("L1_ERROR", str(e))
            return False

        print("[L2] 路径验证...")
        try:
            trust_path = os.path.join(BASE, ".tianshu", "trust_root.json")
            if os.path.exists(trust_path):
                with open(trust_path) as f:
                    trust = json.load(f)
                stored_mount = trust.get("hardware", {}).get("mount_point", "")
                if stored_mount and os.path.abspath(BASE) != os.path.abspath(stored_mount):
                    print(f"  ❌ 路径变化: {stored_mount} → {BASE}")
                    self._trigger_protection("PATH_CHANGE", 
                                            f"{stored_mount} → {BASE}")
                    return False
            print(f"  ✅ 路径一致: {BASE}")
        except Exception as e:
            self._trigger_protection("L2_ERROR", str(e))
            return False

        print("[L3] 完整性验证...")
        try:
            from seal import SealEngine
            se = SealEngine()
            ok, diffs = se.verify()
            if not ok:
                print(f"  ❌ 文件被篡改: {len(diffs)} 处")
                for d in diffs[:5]:
                    print(f"     - {d}")
                self._trigger_protection("TAMPER_DETECTED", diffs[:5])
                return False
            print(f"  ✅ 完整性通过")
        except ImportError:
            pass
        except Exception as e:
            self._trigger_protection("L3_ERROR", str(e))
            return False

        self.checks_passed += 1
        print("\n✅ 天枢 v3.5 启动验证通过")
        return True

    def continuous_monitor(self):
        """持续监控循环。"""
        self.running = True
        print(f"🛡 持续守护已启动（每 {CHECK_INTERVAL}s 检查）...")

        while self.running:
            time.sleep(CHECK_INTERVAL)
            try:
                from bind import verify_binding
                result = verify_binding()
                if not result["match"]:
                    self._trigger_protection("RUNTIME_HARDWARE_CHANGE", result)
                    break
                self.checks_passed += 1
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.checks_failed += 1
                if self.checks_failed > 3:
                    self._trigger_protection("CONSECUTIVE_FAILURES", str(e))
                    break

    def _trigger_protection(self, reason: str, detail=None):
        """触发自毁保护。"""
        print(f"\n🔴 安全违规: {reason}")
        if detail:
            print(f"   详情: {detail}")
        try:
            from self_destruct import execute
            execute(reason, detail)
        except ImportError:
            print("⚠ self_destruct 模块不可用")
            sys.exit(1)


def main():
    import argparse
    p = argparse.ArgumentParser(description='天枢 3.0 守护进程')
    p.add_argument('--verify-only', action='store_true', help='仅验证，不持续监控')
    p.add_argument('--interval', type=int, default=CHECK_INTERVAL, help='检查间隔(秒)')
    args = p.parse_args()

    sentinel = Sentinel()

    if not sentinel.startup_verify():
        sys.exit(1)

    if args.verify_only:
        print("验证完成。")
        return

    sentinel.continuous_monitor()


if __name__ == "__main__":
    if not os.path.exists(os.path.join(BASE, ".tianshu", ".bound")) and not os.path.exists(os.path.join(BASE, ".tianshu", ".host_bound")):
        print("⚠ 载体未绑定。请先运行: python3 bind.py bind")
        sys.exit(0)
    main()

