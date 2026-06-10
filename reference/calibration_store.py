#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Copyright (c) 2026 天枢 Tianshu · 定倾 Dingqing（玄鉴 Xuanjian）
"""
calibration_store.py — 天枢 v4.5 校准历史存储。

使用 SQLite 存储所有校准记录，支持查询和清理。
表结构：id | timestamp | peer_fingerprint | tau_self | tau_peer | deviation | verdict
"""
import sqlite3, os, time, json

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, ".tianshu", "calibrations.db")


class CalibrationStore:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS calibrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                peer_fingerprint TEXT NOT NULL,
                tau_self REAL NOT NULL DEFAULT 0.5,
                tau_peer REAL NOT NULL DEFAULT 0.5,
                deviation REAL NOT NULL DEFAULT 0,
                verdict TEXT NOT NULL DEFAULT 'UNKNOWN'
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cal_ts ON calibrations(timestamp)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cal_peer ON calibrations(peer_fingerprint)
        """)
        self.conn.commit()

    def save(self, peer_fingerprint: str, tau_self: float, tau_peer: float,
             deviation: float, verdict: str):
        self.conn.execute(
            "INSERT INTO calibrations (timestamp, peer_fingerprint, tau_self, tau_peer, deviation, verdict) VALUES (?, ?, ?, ?, ?, ?)",
            (time.time(), peer_fingerprint, tau_self, tau_peer, deviation, verdict)
        )
        self.conn.commit()
        self._prune()

    def get_recent(self, limit: int = 10) -> list:
        rows = self.conn.execute(
            "SELECT timestamp, peer_fingerprint, tau_self, tau_peer, deviation, verdict FROM calibrations ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [
            {
                "timestamp": r[0],
                "peer": r[1],
                "tau_self": r[2],
                "tau_peer": r[3],
                "deviation": r[4],
                "verdict": r[5],
            }
            for r in rows
        ]

    def get_by_peer(self, peer_fingerprint: str, limit: int = 20) -> list:
        rows = self.conn.execute(
            "SELECT timestamp, tau_self, tau_peer, deviation, verdict FROM calibrations WHERE peer_fingerprint = ? ORDER BY timestamp DESC LIMIT ?",
            (peer_fingerprint, limit)
        ).fetchall()
        return [
            {"timestamp": r[0], "tau_self": r[1], "tau_peer": r[2], "deviation": r[3], "verdict": r[4]}
            for r in rows
        ]

    def stats(self) -> dict:
        total = self.conn.execute("SELECT COUNT(*) FROM calibrations").fetchone()[0]
        warnings = self.conn.execute("SELECT COUNT(*) FROM calibrations WHERE verdict = 'WARNING'").fetchone()[0]
        criticals = self.conn.execute("SELECT COUNT(*) FROM calibrations WHERE verdict = 'CRITICAL'").fetchone()[0]
        unique_peers = self.conn.execute("SELECT COUNT(DISTINCT peer_fingerprint) FROM calibrations").fetchone()[0]
        return {
            "total_calibrations": total,
            "warnings": warnings,
            "criticals": criticals,
            "unique_peers": unique_peers,
        }

    def _prune(self, keep: int = 10000):
        count = self.conn.execute("SELECT COUNT(*) FROM calibrations").fetchone()[0]
        if count > keep:
            self.conn.execute(
                "DELETE FROM calibrations WHERE id NOT IN (SELECT id FROM calibrations ORDER BY timestamp DESC LIMIT ?)",
                (keep,)
            )
            self.conn.commit()


if __name__ == "__main__":
    cs = CalibrationStore()
    stats = cs.stats()
    print(f"  校准记录: {stats['total_calibrations']}")
    print(f"  警告: {stats['warnings']}  严重: {stats['criticals']}")
    print(f"  独立节点: {stats['unique_peers']}")
    recent = cs.get_recent(3)
    if recent:
        print(f"  最近校准:")
        for r in recent:
            print(f"    peer={r['peer'][:8]}... τ_self={r['tau_self']:.3f} τ_peer={r['tau_peer']:.3f} Δ={r['deviation']:.3f} {r['verdict']}")
