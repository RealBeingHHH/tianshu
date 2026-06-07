#!/usr/bin/env python3
"""
constellation.py — 天枢 v5.0 星座管理。

协议合规：TIANSHU Protocol v1.0 第六章
- 星座发现：成员清单 + 定期互校准
- 星座共识：τ_consensus = median(所有成员 τ)
- 隔离机制：偏离 >0.15 → 自动隔离
- 成员管理：加入申请 + 投票批准
"""
import json, os, sys, time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
MEMBERS_PATH = os.path.join(BASE, ".tianshu", "constellation_members.json")
QUARANTINE_PATH = os.path.join(BASE, ".tianshu", "quarantine.json")


def get_fingerprint():
    trust_path = os.path.join(BASE, ".tianshu", "trust_root.json")
    if os.path.exists(trust_path):
        with open(trust_path) as f:
            return json.load(f).get("fingerprint", "unknown")[:16]
    return "unknown"


def load_members() -> dict:
    """加载星座成员清单。"""
    if os.path.exists(MEMBERS_PATH):
        with open(MEMBERS_PATH) as f:
            return json.load(f)
    return {}


def save_members(members: dict):
    """保存星座成员清单。"""
    os.makedirs(os.path.dirname(MEMBERS_PATH), exist_ok=True)
    with open(MEMBERS_PATH, 'w') as f:
        json.dump(members, f, indent=2, ensure_ascii=False)


def load_quarantine() -> list:
    """加载隔离清单。"""
    if os.path.exists(QUARANTINE_PATH):
        with open(QUARANTINE_PATH) as f:
            return json.load(f)
    return []


def save_quarantine(qlist: list):
    """保存隔离清单。"""
    os.makedirs(os.path.dirname(QUARANTINE_PATH), exist_ok=True)
    with open(QUARANTINE_PATH, 'w') as f:
        json.dump(qlist, f, indent=2, ensure_ascii=False)


def get_my_tau() -> float:
    """获取当前 τ。"""
    try:
        from challenge import get_current_tau
        return get_current_tau()
    except Exception:
        return 0.5


def constellation_status() -> dict:
    """获取星座当前状态。"""
    members = load_members()
    quarantine = load_quarantine()
    my_fp = get_fingerprint()
    my_tau = get_my_tau()

    # 收集所有成员的 τ（如果有校准数据）
    taus = [my_tau]
    calibrated = 0
    for fp, info in members.items():
        if fp == my_fp:
            continue
        tau = info.get("tau_last_known", 0.5)
        taus.append(tau)
        if tau:
            calibrated += 1

    # 共识 τ = 中位数
    taus.sort()
    consensus = taus[len(taus) // 2] if taus else my_tau

    deviations = {}
    for fp, info in members.items():
        tau = info.get("tau_last_known", 0.5)
        deviations[fp] = round(abs(tau - consensus), 4)
        # 自动隔离检查
        if abs(tau - consensus) > 0.15 and fp not in quarantine:
            quarantine.append(fp)

    save_quarantine(quarantine)

    return {
        "members": len(members) + 1,  # +1 for self
        "calibrated": calibrated,
        "quarantined": len(quarantine),
        "quarantine_list": quarantine,
        "tau_self": my_tau,
        "tau_consensus": round(consensus, 4),
        "fingerprint": my_fp,
    }


def handle_join_request(request: dict) -> dict:
    """
    处理加入星座请求。
    请求格式：{"fingerprint": "...", "seal_proof": "...", "url": "..."}
    """
    fp = request.get("fingerprint", "unknown")
    seal = request.get("seal_proof", "")
    url = request.get("url", "")

    if not fp or not seal:
        return {"status": "rejected", "reason": "缺少 fingerprint 或 seal_proof"}

    members = load_members()
    if fp in members:
        return {"status": "already_member", "fingerprint": fp}

    # 发起 τ 挑战验证
    try:
        from challenge import send_challenge
        result = send_challenge(url)
        if result.get("verdict") == "CRITICAL":
            return {"status": "rejected", "reason": f"τ 偏差过大: {result.get('deviation', 1)}"}
    except Exception as e:
        pass  # 挑战失败不阻止加入，等待后续验证

    members[fp] = {
        "fingerprint": fp,
        "seal_proof": seal,
        "url": url,
        "joined_at": time.time(),
        "tau_last_known": 0.5,
        "calibrations": 0,
    }
    save_members(members)

    # 记录到账本
    _log("MEMBER_JOINED", {"fingerprint": fp, "url": url})

    return {"status": "accepted", "fingerprint": fp}


def handle_vote(vote: dict) -> dict:
    """
    处理投票请求。
    投票格式：{"target_fp": "...", "action": "remove|restore", "voter_fp": "..."}
    """
    target = vote.get("target_fp", "")
    action = vote.get("action", "")
    voter = vote.get("voter_fp", "unknown")

    members = load_members()
    quarantine = load_quarantine()

    if action == "remove":
        if target in members:
            del members[target]
            save_members(members)
            _log("MEMBER_REMOVED", {"fingerprint": target, "voter": voter})
            return {"status": "removed", "fingerprint": target}
        return {"status": "not_found"}

    elif action == "restore":
        if target in quarantine:
            quarantine.remove(target)
            save_quarantine(quarantine)
            _log("MEMBER_RESTORED", {"fingerprint": target, "voter": voter})
            return {"status": "restored", "fingerprint": target}
        return {"status": "not_in_quarantine"}

    return {"status": "unknown_action", "action": action}


def constellation_health_check():
    """对星座所有成员发起挑战，更新 τ。"""
    members = load_members()
    my_fp = get_fingerprint()
    updated = 0

    for fp, info in list(members.items()):
        url = info.get("url", "")
        if not url:
            continue
        try:
            from challenge import send_challenge
            result = send_challenge(url)
            if "error" not in result:
                info["tau_last_known"] = result.get("tau_peer", 0.5)
                info["calibrations"] = info.get("calibrations", 0) + 1
                updated += 1
                _log("CONSTELLATION_CALIBRATION", {
                    "peer": fp,
                    "tau_peer": result.get("tau_peer", 0.5),
                    "verdict": result.get("verdict", "?"),
                })
        except Exception:
            pass

    if updated:
        save_members(members)
    return updated


def _log(event_type: str, detail: dict):
    """记录星座事件到账本。"""
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
    p = argparse.ArgumentParser(description='天枢 v5.0 星座管理')
    p.add_argument('action', choices=['status', 'health', 'join', 'members'],
                   help='status|health|join|members')
    p.add_argument('--url', help='新成员 URL（join 时使用）')
    p.add_argument('--fp', help='目标指纹')
    args = p.parse_args()

    if args.action == 'status':
        s = constellation_status()
        print(f"  成员: {s['members']}  已校准: {s['calibrated']}  隔离: {s['quarantined']}")
        print(f"  τ_self: {s['tau_self']}  τ_consensus: {s['tau_consensus']}")
        print(f"  指纹: {s['fingerprint']}")

    elif args.action == 'health':
        n = constellation_health_check()
        print(f"  健康检查完成: {n} 个成员已更新")

    elif args.action == 'join':
        if not args.url or not args.fp:
            print("  用法: constellation.py join --fp <指纹> --url <http://...>")
        else:
            result = handle_join_request({
                "fingerprint": args.fp,
                "seal_proof": "manual",
                "url": args.url,
            })
            print(f"  {result['status']}: {result.get('fingerprint', '?')}")

    elif args.action == 'members':
        members = load_members()
        q = load_quarantine()
        print(f"  成员 ({len(members)}):")
        for fp, info in members.items():
            in_q = "🚫" if fp in q else "✅"
            print(f"    {in_q} {fp[:12]}... τ={info.get('tau_last_known',0.5):.3f} 校准={info.get('calibrations',0)}")
