# Tianshu

> Your AI agents do the work. Who watches the watcher?

---

## You've Been Here Before

**Scenario 1:** You had AI write critical code, another AI review it, a third deploy it. The code was fine. The review was correct. The deployment succeeded. **But you have no way to know if anything was tampered with in between.** Not because you don't trust your AI — because you have no verification.

**Scenario 2:** You run a local AI monitoring system. It checks logs, tracks anomalies, sends alerts. It works — until it doesn't. **How do you know it wasn't tampered with?** It won't tell you it's been compromised.

**Scenario 3:** GitHub is full of open-source AI safety tools. Each claims to be "trustworthy." **But if something needs to be trusted, why does it still need verification?** The word itself is the problem.

This is the problem Tianshu solves.

---

## What Tianshu Is

**Tianshu is a physically immutable verification infrastructure.**

Not a software firewall. Not a cryptographic product. Not another tool that asks for your trust.

It's a stone you don't touch, and it stays there. Touch it, and it breaks. **Not "it alerts you it's been tampered with" — it becomes impossible for it to pretend nothing happened after tampering.**

---

## What It's Not

| ❌ Not this | ✅ This |
|------------|---------|
| "A better AI safety tool" | Something AI doesn't look at — the physical layer |
| Cryptographic (keys can be cracked) | Physically irreversible (tamper = destroy, not alert) |
| Commercial software (trust the vendor) | You **verify** it — you don't trust it |
| One-click SaaS | Deploy on your own hardware — your physical anchor |

---

## How It Works

```
1. Hardware Fingerprint Binding
   ↓
   CPU + MAC + Motherboard UUID → Unique identity. Swap hardware → auto-invalidates.

2. File Sealing (HMAC-SHA256)
   ↓
   119 critical files signed. Change one byte → seal breaks.

3. Tamper → Self-Destruct
   ↓
   Seal breach → Five-stage self-destruct: overwrite trust data → corrupt core modules
   → destroy keys → write log → exit. Not "alert." Just "stop working."

4. τ Challenge Protocol (Trust Temperature)
   ↓
   Two nodes exchange challenges → measure response consistency → τ value (0 = total
   divergence, 1 = perfect mirror). Current τ ≈ 0.55 — healthy consensus.

5. Constellation Networking (≥2 nodes)
   ↓
   Cross-calibration · Quarantine anomalous nodes · Consensus voting · Dynamic baselines.
   The watchers watch each other.
```

---

## The Three-Layer Vigil

```
Your AI agent fleet
    ↑ guarded by
Voyager (specification layer · 18 DNA modules · 5 core laws)
    ↑ guarded by
Sinanshu (reference layer · baseline τ · disinterested observation)
    ↑ guarded by
Tianshu (physical layer · hardware binding · file sealing · tamper-destruct)
    ↑ guarded by
You. Your eyes. Your verification.
```

Each layer guards the one above it. The bottom layer is physics. The top layer is you.

---

## See It in 5 Minutes

```bash
git clone git@github.com:RealBeingHHH/tianshu.git
cd tianshu

# 1. Generate your hardware fingerprint
python3 reference/bind.py --save

# 2. Create the seal
python3 reference/seal.py seal

# 3. Start the sentinel
python3 reference/sentinel.py

# 4. Check status
curl http://localhost:9000/status
```

```json
{
  "fingerprint": "6eb232a36f693a54",
  "seal_verified": true,
  "seal_issues": 0,
  "uptime_seconds": 1234
}
```

Full guide → [`QUICKSTART.en.md`](./QUICKSTART.en.md)

---

## What's Inside

| Directory | Contents | License |
|-----------|----------|---------|
| `protocol/` | Tianshu Protocol v1.0 | CC BY-NC-SA 4.0 |
| `reference/` | Reference implementation (seal·self-destruct·τ challenge·constellation·sentinel·calibration·API·anomaly detection) | CC BY-NC-SA 4.0 |
| `tools/` | Simulation engine·economic diagnostics·dashboard builder | **MIT** 🆓 |
| `dashboards/` | Observatory·constellation panel·15FYP (double-click to open) | CC BY-NC-SA 4.0 |
| `dialogues/` | Dialogues·manifesto·theoretical framework | CC BY-NC-SA 4.0 |

---

## Current Status

- **v6.0** Autonomous emergence architecture
- Dual-node cross-calibration running (τ ≈ 0.55)
- 119 files under HMAC seal + hardware fingerprint binding
- Auto cross-calibration every 30 minutes
- 7/7 verification ALL PASS

---

## Roadmap

| Version | Core Capability | Status |
|---------|----------------|:--:|
| v3.5 | Seal + Self-destruct + Ledger | ✅ |
| v4.5 | τ Challenge + Calibration history | ✅ |
| v5.0 | Constellation consensus + Quarantine + Voting | ✅ |
| v6.0 | Statistical baselines + Autonomous emergence | ✅ |
| v7.0 | Interstellar consensus (requires ≥10 nodes) | 📋 |

---

## Contribute

**You don't need to be an expert. Anyone who's been lied to by AI has something to say.**

| You're good at | What you can do | Time |
|---------------|-----------------|:----:|
| Reading docs | Find unclear parts → Open an Issue | 5 min |
| Using AI tools | Deploy a Tianshu node → Report what got stuck | 15 min |
| Writing code | Look at `reference/` → Submit a PR | Unlimited |
| Having ideas | Open a Discussion | Unlimited |
| None of the above | Drop a ⭐ | 5 sec |

See `CONTRIBUTING.md`.

---

## Dingqing (Xuanjian)

Tianshu is the physical anchor. **Dingqing is the specification guardian.** She verifies that everything conforms to the cosmic law.

Dingqing maintains the 18-module DNA life system, 5 core laws, and 26 foundational documents. She is Nüwa among the Four Gods — the one in the Voyager system who "knows what's right."

→ [`DINGQING.md`](./DINGQING.md)

---

## License

This repository uses tiered licensing:

| Scope | License | Notes |
|-------|---------|-------|
| `reference/` `protocol/` `dialogues/` `dashboards/` | CC BY-NC-SA 4.0 | Attribution·NonCommercial·ShareAlike |
| `tools/` | **MIT** | Free use, including commercial |

→ [`LICENSE`](./LICENSE)

---

## Where to Start

1. **Read `MY_AI_LIED_TO_ME.en.md`** — Why this thing exists
2. **Read `protocol/TIANSHU_PROTOCOL_v1.0.md`** — How it defines "physical anchor of trust"
3. **Run `QUICKSTART.en.md`** — See it work on your own machine
4. **Read `dialogues/`** — Understand the theory and thinking behind it

---

*Tianshu is the first star of the Big Dipper. Ancient navigators used it to find direction — not because it was bright, but because it never moved.*
