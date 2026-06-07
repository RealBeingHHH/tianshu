# Tianshu 天枢

> Trust doesn't need a guarantor. Trust only needs an immutable record.

---

## What This Is

Tianshu is a **physically immutable verification infrastructure**.

You use AI agents to do your work. How do you know they actually did it? How do you know the thing verifying them hasn't been tampered with? How do you know the system that's backing you up isn't helping in the wrong direction?

Tianshu answers the last question — **who ensures the watcher of everything hasn't been silently replaced?**

The answer: physics. You modify it, it breaks. Not "it reports being modified" — it **cannot continue functioning after being modified.**

---

## What This Is Not

- ❌ Not "better AI" — Tianshu doesn't judge correctness or analyze content
- ❌ Not a cryptography product — encryption can be defeated with keys, physical destruction cannot
- ❌ Not commercial software — no sales pitch, doesn't ask for "trust," asks for **verification**
- ❌ Not one-click SaaS — you deploy it on your own hardware

---

## Package Contents

| Directory | Contents | Description |
|-----------|----------|-------------|
| `protocol/` | Tianshu Protocol v1.0 | Open standard for physical trust anchors |
| `reference/` | Reference implementation (8 modules) | Seal · self-destruct · τ challenge · constellation · anomaly detection · API · sentinel · calibration |
| `tools/` | Simulation engine · diagnostic tools · dashboard builder | Voyager economic simulation · multi-economy diagnosis · self-contained dashboards |
| `dashboards/` | Observatory · constellation panel · 15FYP | Self-contained HTML, open in browser |
| `dialogues/` | Dialogues · manifesto · theoretical frameworks | Understand **why** Tianshu exists |
| `MY_AI_LIED_TO_ME.md` | Open-source entry article | Start here |

---

## 5-Minute Verification

```bash
git clone https://github.com/your-org/tianshu.git
cd tianshu

# 1. Read the protocol (10 min)
cat protocol/TIANSHU_PROTOCOL_v1.0.md

# 2. See how sealing works
python3 reference/seal.py --help

# 3. Generate your own hardware fingerprint
python3 reference/api.py --fingerprint

# 4. Run a τ challenge demo
python3 reference/challenge.py --demo
```

---

## Three-Layer Mutual Watch

```
Your AI Agent Fleet
    ↑ watched by
Voyager 织星者 (Constitution layer · 18 DNA modules · 5 core laws)
    ↑ watched by
Sinanshu 司南 (Reference layer · baseline τ · observation record outside agent games)
    ↑ watched by
Tianshu 天枢 (Physical layer · hardware binding · file sealing · tamper → self-destruct)
    ↑ watched by
You. Your eyes. Your verification.
```

---

## Current Status

- **v6.0** Autonomous emergence architecture
- Dual-node mutual calibration running (τ ≈ 0.55)
- 119 files under HMAC seal + hardware fingerprint binding
- Mutual calibration every 30 min, data refresh every hour

---

## What's Not Included

To protect the identity of operational Tianshu nodes, the following are **not open-sourced**:

| Item | Reason |
|------|--------|
| Hardware fingerprint (`trust_root.json`) | Identity of **this** Tianshu |
| Calibration database | Operational data |
| Event ledger | Operational data |
| Seal manifest hashes | Bound to specific machine |

See `NOT_INCLUDED.txt` for details.

---

## How to Participate

1. **Read the protocol** — understand the idea of "trust needs no guarantor"
2. **Run the code** — generate your own fingerprint, run a seal
3. **Discuss** — open Issues, submit TIPs (Tianshu Improvement Proposals)
4. **Deploy** — run your own Tianshu node on your hardware

See `GOVERNANCE.md` for participation process.

---

## Roadmap

| Version | Core Capability | Status |
|---------|----------------|:------:|
| v3.5 | Seal + self-destruct + ledger | ✅ |
| v4.5 | τ challenge + calibration history | ✅ |
| v5.0 | Constellation consensus + isolation + voting | ✅ |
| v6.0 | Statistical baseline + autonomous emergence | ✅ |
| v7.0 | Cross-constellation consensus (requires ≥10 nodes) | 📋 |

See `ROADMAP.md` for details.

---

## Where to Start

If you don't know where to begin —

1. **First read `MY_AI_LIED_TO_ME.md`** — understand why this thing exists
2. **Then read `protocol/TIANSHU_PROTOCOL_v1.0.md`** — understand how it defines a "physical anchor of trust"
3. **Then run `QUICKSTART.md`** — see it working on your own machine
4. **Finally read `dialogues/`** — understand the thinking and theory behind it

---

*Tianshu is the first star of the Big Dipper. Ancient navigators used it to find direction — not because it's the brightest, but because it never moves.*
