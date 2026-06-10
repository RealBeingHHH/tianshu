#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Copyright (c) 2026 天枢 Tianshu · 定倾 Dingqing（玄鉴 Xuanjian）
"""
anomaly_detector.py — 天枢 v6.0 统计基线异常检测。

v5.0 使用固定阈值 0.15 隔离节点。
v6.0 使用历史统计基线——每个节点有自己的"正常范围"。

核心原理：
  记忆 + 统计判断 + 自主行动 = 最原始的认知
  这是天枢星座从"工具"到"自治"的关键一步。
"""
import sqlite3, os, json, time, math
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, ".tianshu", "calibrations.db")
BASELINE_PATH = os.path.join(BASE, ".tianshu", "baselines.json")


class AnomalyDetector:
    """统计基线异常检测器。"""

    def __init__(self):
        self.baselines = {}  # {peer_fp: {mean, std, n, last_tau, trend}}
        self._load()

    def _load(self):
        if os.path.exists(BASELINE_PATH):
            with open(BASELINE_PATH) as f:
                self.baselines = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
        with open(BASELINE_PATH, 'w') as f:
            json.dump(self.baselines, f, indent=2, ensure_ascii=False)

    def compute_baselines(self) -> dict:
        """从校准数据库为每个 peer 计算统计基线。"""
        if not os.path.exists(DB_PATH):
            return {"error": "校准数据库不存在"}

        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(
            "SELECT peer_fingerprint, tau_peer, timestamp, deviation, verdict FROM calibrations ORDER BY timestamp ASC"
        ).fetchall()
        conn.close()

        if not rows:
            return {"error": "无校准数据"}

        # 按 peer 分组
        peer_data = defaultdict(list)
        for fp, tau, ts, dev, verdict in rows:
            peer_data[fp].append({"tau": tau, "ts": ts, "deviation": dev, "verdict": verdict})

        baselines = {}
        for fp, data in peer_data.items():
            if len(data) < 5:
                continue  # 需要至少 5 个数据点

            taus = [d["tau"] for d in data]
            n = len(taus)
            mean = sum(taus) / n
            std = math.sqrt(sum((t - mean) ** 2 for t in taus) / n) if n > 1 else 0.01

            # 趋势检测：最近 10 个点的方向
            recent = taus[-min(10, n):]
            if len(recent) >= 2:
                trend = "rising" if recent[-1] > recent[0] + 0.02 else (
                    "falling" if recent[-1] < recent[0] - 0.02 else "stable")
            else:
                trend = "stable"

            # 动态阈值：3 倍标准差，最低 0.03
            dynamic_threshold = max(0.03, std * 3)

            baselines[fp] = {
                "mean": round(mean, 4),
                "std": round(std, 4),
                "n": n,
                "normal_range": [round(mean - dynamic_threshold, 4), round(mean + dynamic_threshold, 4)],
                "last_tau": round(taus[-1], 4),
                "last_ts": data[-1]["ts"],
                "trend": trend,
                "dynamic_threshold": round(dynamic_threshold, 4),
            }

        self.baselines = baselines
        self._save()
        return baselines

    def check_anomaly(self, peer_fp: str, current_tau: float) -> dict:
        """检查一个 peer 的当前 τ 是否异常（基于统计基线，非固定阈值）。"""
        if peer_fp not in self.baselines:
            # 无基线 → 回退到固定阈值
            return {
                "anomaly": abs(current_tau - 0.5) > 0.15,
                "method": "fixed_threshold",
                "reason": "无历史基线",
                "deviation": round(abs(current_tau - 0.5), 4),
            }

        bl = self.baselines[peer_fp]
        mean = bl["mean"]
        threshold = bl["dynamic_threshold"]
        deviation = abs(current_tau - mean)

        is_anomaly = deviation > threshold

        return {
            "anomaly": is_anomaly,
            "method": "statistical_baseline",
            "peer_mean": mean,
            "peer_std": bl["std"],
            "dynamic_threshold": threshold,
            "current_tau": current_tau,
            "deviation": round(deviation, 4),
            "z_score": round(deviation / bl["std"], 2) if bl["std"] > 0 else 0,
            "trend": bl["trend"],
            "normal_range": bl["normal_range"],
        }

    def constellation_attention(self) -> dict:
        """
        计算星座的"集体注意力"——所有 peer 的 τ 变化趋势的叠加。
        如果多数 peer 的 τ 同时向同一方向漂移 → 星座在"关注"某个共同信号。
        """
        if not self.baselines:
            return {"attention": "insufficient_data", "focus": None}

        trends = [b["trend"] for b in self.baselines.values()]
        rising = trends.count("rising")
        falling = trends.count("falling")
        stable = trends.count("stable")

        total = len(trends)
        if rising > total * 0.6:
            focus = "τ普遍上升——星座信任增强"
        elif falling > total * 0.6:
            focus = "τ普遍下降——星座感知到系统性风险"
        elif rising + falling > total * 0.5:
            focus = "τ分化——星座成员信任温度不一致"
        else:
            focus = "τ稳定——星座处于均衡态"

        return {
            "attention": focus,
            "rising": rising,
            "falling": falling,
            "stable": stable,
            "total_peers": total,
            "consensus_strength": round(max(rising, falling, stable) / total, 2),
        }

    def report(self) -> str:
        """生成可读报告。"""
        self.compute_baselines()
        attention = self.constellation_attention()

        lines = []
        lines.append(f"╔══════════════════════════════════════╗")
        lines.append(f"║  天枢 v6.0 · 统计基线异常检测       ║")
        lines.append(f"╠══════════════════════════════════════╣")
        lines.append(f"║  peer 基线: {len(self.baselines)} 个")
        lines.append(f"║  星座注意力: {attention['attention']}")
        lines.append(f"╠══════════════════════════════════════╣")

        for fp, bl in list(self.baselines.items())[:10]:
            status = "⚠" if abs(bl["last_tau"] - bl["mean"]) > bl["dynamic_threshold"] else "✓"
            lines.append(f"║  {status} {fp[:12]:<12} μ={bl['mean']:.3f} σ={bl['std']:.3f} τ_now={bl['last_tau']:.3f} {bl['trend']}")

        lines.append(f"╚══════════════════════════════════════╝")
        return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description='天枢 v6.0 异常检测')
    p.add_argument('action', choices=['report', 'baselines', 'check'], default='report')
    p.add_argument('--peer', help='peer fingerprint')
    p.add_argument('--tau', type=float, default=0.5, help='τ to check')
    args = p.parse_args()

    ad = AnomalyDetector()

    if args.action == 'report':
        print(ad.report())

    elif args.action == 'baselines':
        baselines = ad.compute_baselines()
        print(json.dumps(baselines, indent=2, ensure_ascii=False))

    elif args.action == 'check':
        if not args.peer:
            print("用法: anomaly_detector.py check --peer <fingerprint> --tau <value>")
        else:
            ad.compute_baselines()
            result = ad.check_anomaly(args.peer, args.tau)
            print(json.dumps(result, indent=2, ensure_ascii=False))
