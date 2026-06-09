# Tianshu Quickstart Guide

> From zero to running — deploy a Tianshu node on your own hardware

---

## Prerequisites

| Requirement | Minimum | Check Command |
|-------------|---------|---------------|
| Python | 3.9+ | `python3 --version` |
| Linux / WSL / macOS | — | `uname -a` |
| Free disk space | 50MB | `df -h .` |

No Docker, database, GPU, or root access required.

---

## 1. Get the Code

```bash
git clone https://github.com/RealBeingHHH/tianshu.git
cd tianshu
```

Or download the ZIP and extract.

---

## 2. Generate Your Hardware Fingerprint

Every Tianshu node binds to physical hardware via a **host fingerprint**. The fingerprint combines CPU ID + MAC address + motherboard UUID. Changing machines invalidates it.

```bash
python3 reference/bind.py --save
```

Example output:
```
Hardware fingerprint collected → .tianshu/trust_root.json
  Fingerprint: 6eb2f4a1c3d8... (SHA-256 first 32 bits)
  Host bound
```

**This fingerprint is your Tianshu's identity.** Keep it. Don't publish it.

(You can verify the fingerprint anytime with `python3 reference/bind.py --verify`.)

---

## 3. Create the Seal

Sealing = generating HMAC signatures for all critical files. After sealing, any modification to any file — even a single character — breaks the seal.

```bash
python3 reference/seal.py seal
```

Example output:
```
Seal created
  Files:  119
  Algorithm: HMAC-SHA256
  Manifest: .tianshu/sealed_manifest.json
  Host bound: .tianshu/.host_bound
```

After sealing, your Tianshu enters **protected state**.

---

## 4. Start Tianshu

```bash
python3 reference/sentinel.py
```

The sentinel will:

1. Verify seal integrity
2. Verify hardware fingerprint match
3. Start API service (default port 9000)
4. Enter continuous watch mode

Example output:
```
═══════════════════════════════════════
  Tianshu v6.0 · Sentinel Watch Mode
═══════════════════════════════════════
  ✅ Seal verified    (119/119)
  ✅ Fingerprint match (6eb2f4a1)
  ✅ Hardware bound   (host unchanged)
  
  🌐 API: http://localhost:9000
  📊 Status: http://localhost:9000/status
  
  Sentinel ready. Watching...
```

---

## 5. Verify Tianshu Is Working

### Check Status

```bash
curl http://localhost:9000/status
```

Response:
```json
{
  "fingerprint": "6eb232a36f693a54",
  "seal_verified": true,
  "seal_issues": 0,
  "uptime_seconds": 1234
}
```

### Manual Seal Verification

```bash
python3 reference/seal.py verify
```

### View Anomaly Detection Baselines

```bash
python3 reference/anomaly_detector.py baselines
```

---

## 6. Daily Maintenance

### Update Seal (After Adding/Removing Files)

```bash
# Unlock files first (if locked)
sudo chattr -i .tianshu/sealed_manifest.json .tianshu/trust_root.json

# Re-seal
python3 reference/seal.py seal

# Re-lock
sudo chattr +i .tianshu/sealed_manifest.json .tianshu/trust_root.json
```

### View Calibration Records

```bash
python3 reference/calibration_store.py
```

---

## 7. Multi-Node (Constellation Mode)

If you have a second machine to run Tianshu:

### Deploy Node 2

On the second machine, repeat steps 2–4. The default port is 9000 — if both are on the same machine, use different ports for each.

### Join the Constellation

First, find Node 2's fingerprint (check its status page).

On Node 1:

```bash
python3 reference/constellation.py join --url http://node2-ip:9000 --fp <node2-fingerprint>
```

Verify constellation status:

```bash
python3 reference/constellation.py status
```

Example output:
```json
{
  "members": 2,
  "calibrated": 1,
  "quarantined": 0,
  "tau_self": 0.55,
  "tau_consensus": 0.55
}
```

### Run τ Mutual Calibration

```bash
python3 reference/constellation.py health
```

Or challenge a peer directly:

```bash
python3 reference/challenge.py challenge http://node2-ip:9000
```

---

## 8. Security Hardening (Optional but Recommended)

### 1. Lock Files as Immutable (Linux)

```bash
# After sealing, prevent file modification
sudo chattr +i .tianshu/trust_root.json
sudo chattr +i .tianshu/sealed_manifest.json
```

**Note**: After locking, you must `chattr -i` before updating the seal.

### 2. Configure Self-Destruct Policy

Edit `.tianshu/destruct_policy.json` (auto-generated after first deployment):

```json
{
  "triggers": {
    "seal_breach": "immediate",
    "fingerprint_mismatch": "immediate",
    "unauthorized_file_access": "log_only",
    "network_isolation_24h": "self_destruct"
  },
  "destruct_method": "overwrite_then_remove"
}
```

### 3. View Self-Destruct Log

```bash
cat .tianshu/destruction.log
```

---

## 9. Dashboards

Tianshu includes three self-contained HTML panels. No server needed — open in any browser:

| Panel | File | Purpose |
|-------|------|---------|
| Observatory | `dashboards/observatory.html` | Voyager system overview |
| Constellation | `dashboards/tianshu_constellation.html` | Multi-node τ comparison |
| 15FYP | `dashboards/15fyp_dashboard.html` | Economic simulation |

---

## 10. Run the Simulation Engine (Optional)

The simulation engine demonstrates Voyager's multi-agent economic system:

```bash
# Six-economy comparison
python3 tools/simulate_enhanced.py

# China economy only
python3 tools/simulate_enhanced.py --economy cn

# Enable Voyager mode (ε_v jump)
python3 tools/simulate_enhanced.py --voyager

# Economic diagnosis
python3 tools/voyager_diagnose.py

# US economy only
python3 tools/voyager_diagnose.py --economy us
```

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `sentinel.py` says "载体未绑定" (host unbound) | No seal exists | Run `bind.py --save` then `seal.py seal` |
| `seal.py seal` can't find files | Not in tianshu directory | `cd tianshu` |
| Fingerprint mismatch | Hardware changed | Re-run `bind.py --save` |
| Seal verification fails | Files modified | Check for accidental changes, or re-run `seal.py seal` |
| API port in use | Another process on 9000 | Kill old process or use different port |
| `chattr: Operation not permitted` | WSL drvfs mount | Skip chattr on WSL (native Linux only) |
| Self-destruct triggered | Seal breach or hardware change | Check `.tianshu/destruction.log` |

---

## Next Steps

- Read `protocol/TIANSHU_PROTOCOL_v1.0.md` — understand the protocol design
- Read `GOVERNANCE.md` — learn how to participate in improvements
- Read `dialogues/` — understand the philosophy and theory behind it
- Integrate Tianshu API into your AI agent workflow

---

*Tianshu is not what you believe in. It's what you verify.*
