#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Copyright (c) 2026 天枢 Tianshu · 定倾 Dingqing（玄鉴 Xuanjian）
"""
api.py — FastAPI REST + WebSocket server for Voyager.

Endpoints:
  GET  /api/health          — System health
  GET  /api/agents          — List all agents with current η
  GET  /api/agents/<id>     — Agent detail + history
  GET  /api/rounds          — Round history
  GET  /api/geometric       — Geometric analysis trend
  POST /api/intervene       — Trigger intervention
  GET  /api/db/stats        — Database statistics
  WS   /ws                  — Real-time pipeline events

Usage:
  python3 api.py                    
  python3 api.py --port 9000        
  python3 api.py --with-runtime     
"""
import sys, os, json, time, threading

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("⚠ FastAPI not installed. Run: pip install fastapi uvicorn")
    print("  Falling back to basic http.server mode...")

if HAS_FASTAPI:
    app = FastAPI(title="织星者 Voyager API", version="1.0")
    START_TIME = time.time()
    
    class WSManager:
        def __init__(self):
            self.clients: list = []
        async def broadcast(self, data: dict):
            dead = []
            for ws in self.clients:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
            for d in dead:
                self.clients.remove(d)
    
    ws_manager = WSManager()
    
    def _get_db():
        try:
            from core.persistence import get_db
            return get_db()
        except Exception:
            return None
    
    
    @app.get("/api/health")
    async def health():
        db = _get_db()
        stats = db.stats() if db else {}
        return {
            "status": "ok",
            "version": "1.0",
            "agents": stats.get("agents", 0),
            "rounds": stats.get("rounds", 0),
            "db_size_kb": stats.get("db_size_kb", 0),
        }
    
    @app.get("/api/agents")
    async def list_agents():
        db = _get_db()
        if not db:
            return {"agents": [], "error": "DB not available"}
        agents = db.get_agents()
        latest = db.get_latest_etas()
        result = []
        for a in agents:
            aid = a["id"]
            eta_info = latest.get(aid, {})
            result.append({
                "id": aid,
                "name": a.get("name", aid),
                "role": a.get("role", "unknown"),
                "eta": eta_info.get("eta", 0.5),
                "label": eta_info.get("label", "?"),
                "last_round": eta_info.get("round", 0),
            })
        return {"agents": result, "count": len(result)}
    
    @app.get("/api/agents/{agent_id}")
    async def agent_detail(agent_id: str):
        db = _get_db()
        if not db:
            return {"error": "DB not available"}
        history = db.get_agent_history(agent_id, limit=50)
        trend = db.get_eta_trend(agent_id, window=20)
        interventions = db.intervention_count(agent_id)
        return {
            "agent_id": agent_id,
            "history": history,
            "eta_trend": trend,
            "current_eta": trend[-1] if trend else 0.5,
            "interventions": interventions,
        }
    
    @app.get("/api/rounds")
    async def rounds(limit: int = 20):
        db = _get_db()
        if not db:
            return {"rounds": [], "error": "DB not available"}
        return {"rounds": db.get_round_history(limit)}
    
    @app.get("/api/geometric")
    async def geometric(limit: int = 20):
        db = _get_db()
        if not db:
            return {"trend": [], "error": "DB not available"}
        return {"trend": db.get_geometric_trend(limit)}
    
    @app.post("/api/intervene")
    async def intervene(data: dict):
        agent_id = data.get("agent_id")
        action = data.get("action", "WARN")
        reason = data.get("reason", "manual")
        db = _get_db()
        if db:
            db.save_intervention(0, agent_id, action, reason)
        if ws_manager.clients:
            await ws_manager.broadcast({
                "event": "intervention",
                "agent_id": agent_id,
                "action": action,
                "reason": reason,
                "timestamp": time.time(),
            })
        return {"status": "ok", "agent_id": agent_id, "action": action}
    
    @app.get("/api/db/stats")
    async def db_stats():
        db = _get_db()
        if not db:
            return {"error": "DB not available"}
        return db.stats()
    
    @app.get("/api/db/status")
    async def db_status():
        db = _get_db()
        if not db:
            return {"status": "disconnected"}
        s = db.stats()
        return {"status": "connected", "size_kb": s["db_size_kb"],
                "agents": s["agents"], "rounds": s["rounds"]}
    
    

    # ═══ 天枢 v3.5: 公开账本 & 状态端点 ═══


    @app.post("/challenge")
    async def tianshu_challenge(request: dict):
        """POST /challenge — τ 挑战协议端点"""
        try:
            from challenge import handle_challenge
            return handle_challenge(request)
        except Exception as e:
            return {"error": str(e), "responder_id": "unknown"}


    # ═══ 天枢 v5.0: 星座端点 ═══

    @app.get("/constellation/status")
    async def constellation_status():
        try:
            from constellation import constellation_status
            return constellation_status()
        except Exception as e:
            return {"error": str(e)}

    @app.post("/constellation/join")
    async def constellation_join(request: dict):
        try:
            from constellation import handle_join_request
            return handle_join_request(request)
        except Exception as e:
            return {"error": str(e)}

    @app.post("/constellation/vote")
    async def constellation_vote(request: dict):
        try:
            from constellation import handle_vote
            return handle_vote(request)
        except Exception as e:
            return {"error": str(e)}


    @app.get("/anomaly/report")
    async def anomaly_report():
        try:
            from anomaly_detector import AnomalyDetector
            ad = AnomalyDetector()
            ad.compute_baselines()
            return {
                "baselines": ad.baselines,
                "constellation_attention": ad.constellation_attention(),
            }
        except Exception as e:
            return {"error": str(e)}

    @app.get("/status")
    async def tianshu_status():
        try:
            from seal import SealEngine
            se = SealEngine()
            ok, diffs = se.verify()
        except: ok, diffs = False, ["seal error"]
        fingerprint = "unknown"
        try:
            tp = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tianshu", "trust_root.json")
            if os.path.exists(tp):
                with open(tp) as f: fingerprint = json.load(f).get("fingerprint", "unknown")[:16]
        except: pass
        return {"fingerprint": fingerprint, "seal_verified": ok, "seal_issues": len(diffs), "uptime_seconds": int(time.time() - START_TIME)}

    @app.get("/ledger/latest")
    async def ledger_latest(n: int = 100):
        lp = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tianshu", "ledger.jsonl")
        entries = []
        if os.path.exists(lp):
            with open(lp) as f:
                for line in list(f.readlines())[-n:]:
                    try: entries.append(json.loads(line))
                    except: pass
        return {"entries": entries, "count": len(entries)}

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await websocket.accept()
        ws_manager.clients.append(websocket)
        try:
            await websocket.send_json({"event": "connected", "msg": "Welcome to Voyager"})
            while True:
                data = await websocket.receive_text()
                await websocket.send_json({"event": "echo", "data": data})
        except WebSocketDisconnect:
            ws_manager.clients.remove(websocket)
        except Exception:
            if websocket in ws_manager.clients:
                ws_manager.clients.remove(websocket)
    
    
    @app.get("/")
    async def dashboard():
        """Serve a lightweight live dashboard."""
        return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="zh">
    <head><meta charset="UTF-8"><title>织星者 Voyager</title>
    <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#0a0a0a;color:#e0e0e0;font-family:monospace;padding:20px}
    h1{color:#00ff88;margin-bottom:20px}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:15px}
    .card{background:#1a1a2e;border-radius:8px;padding:15px;border:1px solid 
    .card h3{color:#00ff88;margin-bottom:10px;font-size:14px}
    .bar{height:12px;background:#222;border-radius:6px;overflow:hidden;margin:4px 0}
    .bar-fill{height:100%;border-radius:6px;transition:width .3s}
    .green{background:#00ff88}.yellow{background:#ffcc00}.red{background:#ff4444}
    .agent-row{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid 
    .eta-val{font-weight:bold;min-width:50px;text-align:right}
    button{background:#00ff88;color:#0a0a0a;border:none;padding:8px 16px;border-radius:4px;cursor:pointer;font-weight:bold;margin:4px}
    button:hover{opacity:.8}
    .status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
    .dot-green{background:#00ff88}.dot-yellow{background:#ffcc00}.dot-red{background:#ff4444}
    </style></head>
    <body>
    <h1>🛰 织星者 Voyager Dashboard</h1>
    <div class="grid">
        <div class="card"><h3>System</h3><div id="sys"></div></div>
        <div class="card"><h3>Agents</h3><div id="agents"></div></div>
        <div class="card"><h3>Rounds</h3><div id="rounds"></div></div>
        <div class="card"><h3>Geometric</h3><div id="geo"></div></div>
        <div class="card"><h3>Actions</h3>
            <button onclick="fetch('/api/intervene',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:'test',action:'WARN',reason:'dashboard'})})">Send Test</button>
        </div>
    </div>
    <script>
    async function refresh(){
        try{
            let r=await fetch('/api/health');let h=await r.json();
            document.getElementById('sys').innerHTML=`<span class="status-dot dot-green"></span>v${h.version} | ${h.agents} agents | ${h.rounds} rounds | ${h.db_size_kb}KB`;
            
            r=await fetch('/api/agents');let a=await r.json();
            let html='';
            (a.agents||[]).forEach(ag=>{
                let w=Math.round(ag.eta*100);
                let c=w>70?'green':w>40?'yellow':'red';
                html+=`<div class="agent-row"><span>${ag.id}</span><span class="eta-val">${ag.eta.toFixed(3)}</span></div><div class="bar"><div class="bar-fill ${c}" style="width:${w}%"></div></div>`;
            });
            document.getElementById('agents').innerHTML=html||'No agents';
            
            r=await fetch('/api/rounds?limit=5');let rd=await r.json();
            html=(rd.rounds||[]).map(r=>`<div class="agent-row"><span>Round ${r.round}</span><span class="eta-val">${r.avg_eta.toFixed(3)}</span><span>${r.health}</span></div>`).join('');
            document.getElementById('rounds').innerHTML=html||'No rounds';
            
            r=await fetch('/api/geometric?limit=5');let g=await r.json();
            html=(g.trend||[]).map(r=>`<div class="agent-row"><span>R${r.round}</span><span>κ=${r.curvature_mean.toFixed(2)}</span><span>C=${r.compressibility.toFixed(2)}</span><span>${r.health}</span></div>`).join('');
            document.getElementById('geo').innerHTML=html||'No data';
        }catch(e){}
    }
    refresh();setInterval(refresh,3000);
    </script></body></html>""")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description='织星者 API Server')
    p.add_argument('--port', type=int, default=8000)
    p.add_argument('--host', default='0.0.0.0')
    p.add_argument('--with-runtime', action='store_true')
    args = p.parse_args()

    if not HAS_FASTAPI:
        print("Starting basic server...")
        import http.server
        os.chdir(BASE)
        http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=args.port)
    else:
        if args.with_runtime:
            import threading
            def start_runtime():
                import time
                time.sleep(2)  
                from runtime import AgentPool
                pool = AgentPool()
                pool.run()
            threading.Thread(target=start_runtime, daemon=True).start()
            print("🚀 Agent Runtime starting in background...")

        print(f"🚀 Voyager API: http://{args.host}:{args.port}")
        print(f"   Dashboard: http://localhost:{args.port}/")
        print(f"   API Docs:  http://localhost:{args.port}/docs")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")

