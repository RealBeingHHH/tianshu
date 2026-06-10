#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Copyright (c) 2026 天枢 Tianshu · 定倾 Dingqing（玄鉴 Xuanjian）
"""
challenge.py — 天枢 v4.5 τ 挑战协议。

协议合规：TIANSHU Protocol v1.0 第四章
- 服务端：接收挑战请求 → 验证 → 返回 τ 响应
- 客户端：发起挑战 → 比对 τ → 记录校准结果
- 三档判决：NORMAL (<0.05) / WARNING (0.05-0.15) / CRITICAL (≥0.15)
"""
import json, time, hashlib, hmac, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)


def get_fingerprint():
    """获取当前天枢指纹的前 16 位。"""
    trust_path = os.path.join(BASE, ".tianshu", "trust_root.json")
    if os.path.exists(trust_path):
        with open(trust_path) as f:
            return json.load(f).get("fingerprint", "unknown")[:16]
    return "unknown"


def get_current_tau():
    """
    从 seal 验证状态和当前系统状态计算 τ。
    τ = 封印完整性 × 信任根哈希稳定性 × 运行时长因子
    """
    tau = 0.5  # 默认 τ

    # 封印验证
    try:
        from seal import SealEngine
        se = SealEngine()
        ok, diffs = se.verify()
        if not ok:
            tau -= 0.05 * min(len(diffs), 5)
        else:
            tau += 0.05
    except Exception:
        tau -= 0.1

    # 信任根哈希
    trust_path = os.path.join(BASE, ".tianshu", "trust_root.json")
    if os.path.exists(trust_path):
        with open(trust_path) as f:
            trust = json.load(f)
        manifest_hash = trust.get("sealed_manifest_hash", "")
        if manifest_hash:
            tau += 0.02

    return round(max(0.1, min(0.95, tau)), 4)


def get_tau_history(limit=10):
    """从校准数据库读取最近 N 条 τ 记录。"""
    try:
        from calibration_store import CalibrationStore
        cs = CalibrationStore()
        return cs.get_recent(limit)
    except Exception:
        return []


def get_seal_proof():
    """获取封印验证证明（签名前 16 位）。"""
    manifest_path = os.path.join(BASE, ".tianshu", "sealed_manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            sealed = json.load(f)
        sig = sealed.get("signature", "")
        return sig[:16] if sig else "unsealed"
    return "unsealed"


def sign_response(response: dict) -> str:
    """用硬件指纹派生密钥对响应签名。"""
    fp = get_fingerprint()
    key = hashlib.pbkdf2_hmac('sha256', fp.encode(), b'TIANSHU_CHALLENGE_V1', 10000, dklen=32)
    payload = json.dumps(response, sort_keys=True, ensure_ascii=False).encode()
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def handle_challenge(request: dict) -> dict:
    """
    处理 τ 挑战请求。
    
    请求格式：
    {
        "challenger_id": "挑战者指纹前16位",
        "challenge_type": "TAU",
        "reference_value": 0.5,
        "challenge_nonce": "随机数",
        "timestamp": "ISO8601"
    }
    """
    challenger_id = request.get("challenger_id", "unknown")
    challenge_nonce = request.get("challenge_nonce", "")

    current_tau = get_current_tau()
    tau_history = get_tau_history(5)
    seal_proof = get_seal_proof()

    response = {
        "responder_id": get_fingerprint(),
        "challenge_type": "TAU",
        "challenge_nonce": challenge_nonce,
        "tau_value": current_tau,
        "tau_history": tau_history,
        "seal_proof": seal_proof,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    response["signature"] = sign_response(response)

    # 记录到账本
    _log_to_ledger("CHALLENGE_RECEIVED", {
        "challenger": challenger_id,
        "tau_returned": current_tau,
        "nonce": challenge_nonce,
    })

    return response


def send_challenge(peer_url: str) -> dict:
    """
    向 peer 天枢发起 τ 挑战。
    返回比对结果。
    """
    import urllib.request

    my_tau = get_current_tau()
    nonce = hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]

    request_body = {
        "challenger_id": get_fingerprint(),
        "challenge_type": "TAU",
        "reference_value": my_tau,
        "challenge_nonce": nonce,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        req = urllib.request.Request(
            f"{peer_url}/challenge",
            data=json.dumps(request_body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            response = json.loads(resp.read().decode())

        peer_tau = response.get("tau_value", 0.5)
        peer_id = response.get("responder_id", "unknown")
        deviation = abs(my_tau - peer_tau)

        if deviation < 0.05:
            verdict = "NORMAL"
        elif deviation < 0.15:
            verdict = "WARNING"
        else:
            verdict = "CRITICAL"

        result = {
            "peer": peer_id,
            "peer_url": peer_url,
            "tau_self": my_tau,
            "tau_peer": peer_tau,
            "deviation": round(deviation, 4),
            "verdict": verdict,
            "seal_proof": response.get("seal_proof", "?"),
            "timestamp": time.time(),
        }

        # 存入校准数据库
        _save_calibration(result)

        # 记录到账本
        _log_to_ledger("CHALLENGE_SENT", result)

        return result

    except Exception as e:
        return {"error": str(e), "peer": peer_url, "verdict": "ERROR"}


def _save_calibration(result: dict):
    """保存校准结果到数据库。"""
    try:
        from calibration_store import CalibrationStore
        cs = CalibrationStore()
        cs.save(
            peer_fingerprint=result.get("peer", "unknown"),
            tau_self=result.get("tau_self", 0.5),
            tau_peer=result.get("tau_peer", 0.5),
            deviation=result.get("deviation", 0),
            verdict=result.get("verdict", "ERROR"),
        )
    except Exception:
        pass


def _log_to_ledger(event_type: str, detail: dict):
    """追加事件到公开账本。"""
    ledger_path = os.path.join(BASE, ".tianshu", "ledger.jsonl")
    entry = {
        "timestamp": time.time(),
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event_type": event_type,
        "fingerprint": get_fingerprint(),
        "detail": detail,
    }
    try:
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
        with open(ledger_path, 'a') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description='天枢 v4.5 τ 挑战协议')
    p.add_argument('action', choices=['status', 'challenge'], help='status|challenge <peer_url>')
    p.add_argument('peer', nargs='?', help='peer URL for challenge')
    args = p.parse_args()

    if args.action == 'status':
        tau = get_current_tau()
        fp = get_fingerprint()
        seal = get_seal_proof()
        print(f"  指纹: {fp}")
        print(f"  τ: {tau}")
        print(f"  封印: {seal}")

    elif args.action == 'challenge':
        if not args.peer:
            print("  用法: python3 challenge.py challenge http://peer:8765")
            sys.exit(1)
        result = send_challenge(args.peer)
        if "error" in result:
            print(f"  ❌ {result['error']}")
        else:
            print(f"  peer: {result['peer']}")
            print(f"  τ_self: {result['tau_self']}  τ_peer: {result['tau_peer']}")
            print(f"  偏差: {result['deviation']}  →  {result['verdict']}")
