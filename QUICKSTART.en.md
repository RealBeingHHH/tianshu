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
git clone https://github.com/your-org/tianshu.git
cd tianshu
```

Or download the ZIP and extract.

---

## 2. Generate Your Hardware Fingerprint

Every Tianshu node binds to physical hardware via a **host fingerprint**. The fingerprint combines CPU ID + MAC address + motherboard UUID. Changing machines invalidates it.

```bash
python3 reference/api.py --fingerprint
```

Example output:
```
Host Fingerprint: 6eb2f4a1c3d8... (SHA-256 first 32 bits)
Saved to: .tianshu/trust_root.json
```

**This fingerprint is your Tianshu's identity.** Keep it. Don't publish it.

---

## 3. Create the Seal

Sealing = generating HMAC signatures for all critical files. After sealing, any modification to any file — even a single character — breaks the seal.

```bash
python3 reference/seal.py --init
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
  "node_id": "6eb2f4a1",
  "τ": 0.55,
  "seal": "intact",
  "uptime": "2h 14m",
  "files_sealed": 119,
  "constellation_peers": 1
}
```

### Manual Seal Verification

```bash
python3 reference/seal.py --verify
```

### Run τ Challenge (Calibration Test)

```bash
python3 reference/challenge.py --demo
```

Example output:
```
τ Challenge complete
  Rounds:  3
  τ mean:  0.551
  Deviation: ±0.003
  Status:  ✅ Within baseline range
```

---

## 6. Daily Maintenance

### Check Sentinel Status

```bash
python3 reference/sentinel.py --status
```

### Update Seal (After Adding/Removing Files)

```bash
python3 reference/seal.py --update
```

### View Calibration History

```bash
python3 reference/calibration_store.py --history
```

### View Anomaly Detection Baseline

```bash
python3 reference/anomaly_detector.py --baseline
```

---

## 7. Multi-Node (Constellation Mode)

If you have a second machine to run Tianshu:

### Deploy Node 2

On the second machine, repeat steps 2–4. Use a different port:

```bash
python3 reference/sentinel.py --port 9001
```

### Establish Mutual Calibration

On Node 1:

```bash
python3 reference/constellation.py --add-peer http://node2-ip:9001
```

After this, both nodes will:
- Mutually calibrate τ every 30 minutes
- Share anomaly baselines
- Cross-verify seal integrity

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

Test self-destruct logic (won't actually destroy):

```bash
python3 reference/self_destruct.py --dry-run
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

# Economic diagnosis
python3 tools/voyager_diagnose.py
```

---

## Troubleshooting

| Symptom | Likely Cause | Solution |
|---------|-------------|----------|
| `sentinel.py` fails to start | No seal exists | Run `seal.py --init` first |
| Fingerprint mismatch | Hardware changed | Re-run `api.py --fingerprint` |
| Seal verification fails | Files modified | Check for accidental changes, or `seal.py --update` |
| API port in use | Another process on 9000 | Use `--port 9001` |
| Self-destruct triggered | Seal breach or hardware change | Check `.tianshu/destruction.log` |

---

## Next Steps

- Read `protocol/TIANSHU_PROTOCOL_v1.0.md` — understand the protocol design
- Read `GOVERNANCE.md` — learn how to participate in improvements
- Read `dialogues/` — understand the philosophy and theory behind it
- Integrate Tianshu API into your AI agent workflow

---

*Tianshu is not what you believe in. It's what you verify.*
