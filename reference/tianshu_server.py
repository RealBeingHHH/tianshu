#!/usr/bin/env python3
"""
tianshu_server.py — 天枢 HTTP 服务 · 信标 + 语音 + 分析。

启动后提供完整的 HTTP API + 自然语言指令接口。
独立运行，不依赖 Hermes 或特定部署环境。

用法:
    python3 tianshu_server.py                    # 启动 :9876
    python3 tianshu_server.py --port 9000        # 自定义端口
    python3 tianshu_server.py --auto-wake        # 启动后自动就绪

API 端点:
    GET  /beacon         → 信标状态
    GET  /status         → 详细状态 + 封印信息
    GET  /verify         → 三重验证 (L1+L2+L3)
    POST /wake           → 启动监管
    POST /command        → 语音指令 {"text": "天枢，检测目标"}
    POST /analyze        → 深度分析
    POST /sleep          → 休眠
    POST /shutdown       → 关闭服务

语音指令:
    唤醒天枢             → 启动/部署
    天枢，检测目标        → 分析当前 AI 活动
    天枢，深度分析        → 意图+织星者评估
    天枢，优化方案        → 优化建议
    天枢，报告状态        → 播报目标状态
    天枢，监控面板        → 打开仪表盘
    天枢休眠              → 停止监控
"""

import sys, os, json, time, threading, re
import http.server, socketserver

BASE = os.path.dirname(os.path.abspath(__file__))
BEACON_PORT = 9876
BEACON_FILE = os.path.expanduser("~/.tianshu_beacon")

# ── 语音指令定义 ──────────────────────────────────────────────

COMMANDS = {
    "唤醒天枢": {
        "action": "wake",
        "keywords": ["唤醒天枢", "唤醒", "天枢启动", "启动天枢"],
        "response": "天枢已唤醒。等待指令。",
    },
    "检测目标": {
        "action": "detect",
        "keywords": ["检测目标", "检测", "扫描", "看看", "在做什么"],
        "response": "检测完成。{result}",
    },
    "深度分析": {
        "action": "analyze",
        "keywords": ["深度分析", "分析", "评估"],
        "response": "分析完成。{result}",
    },
    "优化方案": {
        "action": "optimize",
        "keywords": ["优化", "方案", "建议", "改善"],
        "response": "优化建议: {result}",
    },
    "报告状态": {
        "action": "status",
        "keywords": ["报告", "状态", "情况", "怎么样"],
        "response": "当前状态: {result}",
    },
    "监控面板": {
        "action": "dashboard",
        "keywords": ["面板", "仪表盘", "dashboard", "监控面板"],
        "response": "仪表盘已打开: {result}",
    },
    "天枢休眠": {
        "action": "sleep",
        "keywords": ["休眠", "停止", "关闭", "暂停"],
        "response": "天枢休眠中。POST /wake 唤醒。",
    },
}


def match_command(text: str) -> dict:
    """关键词匹配语音指令。"""
    text_lower = text.lower().replace(" ", "")
    best = None
    best_len = 0
    for name, cmd in COMMANDS.items():
        for kw in cmd["keywords"]:
            kw_clean = kw.lower().replace(" ", "")
            if kw_clean in text_lower and len(kw_clean) > best_len:
                best = {"name": name, **cmd}
                best_len = len(kw_clean)
    return best


# ── 分析引擎 ──────────────────────────────────────────────────

class TianshuAnalyzer:
    """深度分析引擎。"""

    def full_analysis(self, context: str = "") -> dict:
        """对当前上下文进行活动+意图+织星者全链路分析。"""
        result = {
            "activity": self._detect_activity(context),
            "intent": self._infer_intent(context),
            "honesty": self._estimate_eta(),
            "health": self._check_health(),
        }
        return result

    def _detect_activity(self, context: str) -> dict:
        """检测当前活动类型。"""
        patterns = {
            "coding": ["代码", "code", "写", "修复", "fix", "bug", "函数", "模块"],
            "research": ["研究", "分析", "调研", "research", "论文", "理论"],
            "debugging": ["调试", "debug", "错误", "error", "排查", "崩溃"],
            "writing": ["写", "文档", "文章", "报告", "总结", "翻译"],
            "conversation": ["对话", "讨论", "聊天", "问", "答"],
            "idle": [],
        }
        scores = {}
        for activity, keywords in patterns.items():
            score = sum(1 for kw in keywords if kw in context)
            scores[activity] = score
        best = max(scores, key=scores.get)
        confidence = min(1.0, scores[best] / max(3, len(patterns[best]) or 1))
        return {"type": best, "confidence": round(confidence, 2)}

    def _infer_intent(self, context: str) -> dict:
        """推断意图。"""
        intents = {
            "build_feature": ["添加", "新增", "实现", "创建", "造", "写"],
            "fix_bug": ["修复", "修", "fix", "bug", "错误"],
            "explore": ["了解", "研究", "看看", "探索", "分析"],
            "deploy": ["部署", "发布", "上线", "推送", "push"],
            "refactor": ["重构", "优化", "整理", "清理"],
        }
        scores = {}
        for intent, keywords in intents.items():
            scores[intent] = sum(1 for kw in keywords if kw in context)
        best = max(scores, key=scores.get)
        return {"primary": best, "confidence": round(min(1.0, scores[best] / 3), 2)}

    def _estimate_eta(self) -> dict:
        """估算当前对话诚实度 (η)。基础版——基于本地校验状态。"""
        sealed = os.path.exists(os.path.join(BASE, ".tianshu", "sealed_manifest.json"))
        bound = os.path.exists(os.path.join(BASE, ".tianshu", ".bound"))
        eta = 0.85 if (sealed and bound) else 0.60
        return {"η": eta, "sealed": sealed, "bound": bound}

    def _check_health(self) -> dict:
        """健康检查。"""
        try:
            from seal import SealEngine
            se = SealEngine()
            ok, diffs = se.verify()
            return {"seal": "intact" if ok else f"breached ({len(diffs)} diffs)",
                    "files_check": len(diffs) == 0}
        except Exception:
            return {"seal": "unavailable"}


# ── 信标状态 ──────────────────────────────────────────────────

_beacon_state = {
    "name": "天枢",
    "version": "6.0",
    "base_path": BASE,
    "started_at": time.time(),
    "status": "idle",
    "bound": False,
    "sealed": False,
    "last_check": None,
}

_analyzer = TianshuAnalyzer()


# ── HTTP 服务 ──────────────────────────────────────────────────

class TianshuHandler(http.server.BaseHTTPRequestHandler):
    """天枢 HTTP 请求处理器。"""

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode())

    def do_GET(self):
        if self.path in ("/beacon", "/"):
            self._json({**_beacon_state, "message": "天枢在线。POST /wake 唤醒。"})

        elif self.path == "/status":
            s = _beacon_state.copy()
            try:
                from seal import SealEngine
                ok, _ = SealEngine().verify()
                s["sealed"] = ok
            except Exception:
                pass
            try:
                hw = os.path.join(BASE, ".tianshu", "trust_root.json")
                if os.path.exists(hw):
                    with open(hw) as f:
                        s["fingerprint"] = json.load(f).get("fingerprint", "?")[:16]
            except Exception:
                pass
            self._json(s)

        elif self.path == "/verify":
            try:
                from sentinel import Sentinel
                ok = Sentinel().startup_verify()
                self._json({"verified": ok})
            except Exception as e:
                self._json({"verified": False, "error": str(e)}, 500)

        elif self.path == "/shutdown":
            self._json({"message": "关闭中..."})
            threading.Timer(0.5, lambda: os._exit(0)).start()

        else:
            self._json({"error": "unknown endpoint"}, 404)

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len)) if content_len > 0 else {}

        if self.path == "/wake":
            _beacon_state["bound"] = os.path.exists(
                os.path.join(BASE, ".tianshu", ".bound"))
            _beacon_state["sealed"] = os.path.exists(
                os.path.join(BASE, ".tianshu", "sealed_manifest.json"))
            _beacon_state["status"] = "monitoring"
            self._json({
                "woken": True,
                "bound": _beacon_state["bound"],
                "sealed": _beacon_state["sealed"],
                "fingerprint": os.path.exists(
                    os.path.join(BASE, ".tianshu", "trust_root.json")),
                "message": "天枢已唤醒。",
            })

        elif self.path == "/command":
            text = body.get("text", "")
            cmd = match_command(text)
            if not cmd:
                self._json({"text": text, "response": f"未识别的指令: '{text}'",
                            "available": list(COMMANDS.keys())})
                return

            action = cmd["action"]
            result = ""

            if action == "wake":
                _beacon_state["status"] = "monitoring"
                result = "天枢已唤醒。等待指令。"
            elif action == "detect":
                a = _analyzer._detect_activity(text)
                result = f"当前活动: {a['type']} (置信度 {a['confidence']})"
            elif action == "analyze":
                analysis = _analyzer.full_analysis(text)
                result = json.dumps(analysis, ensure_ascii=False)
            elif action == "optimize":
                analysis = _analyzer.full_analysis(text)
                result = f"η={analysis['honesty']['η']}, 封印={'完整' if analysis['honesty']['sealed'] else '缺失'}"
            elif action == "status":
                try:
                    from seal import SealEngine
                    ok, diffs = SealEngine().verify()
                    result = f"封印: {'完整' if ok else f'{len(diffs)}处异常'} | "
                except Exception:
                    result = "封印: 未初始化 | "
                result += f"绑定: {'是' if _beacon_state['bound'] else '否'}"
            elif action == "dashboard":
                result = "http://localhost:8765 (仪表盘服务需单独启动)"
            elif action == "sleep":
                _beacon_state["status"] = "idle"
                result = "天枢休眠中。"

            self._json({"text": text, "action": action,
                        "response": cmd["response"].format(result=result)})

        elif self.path == "/analyze":
            analysis = _analyzer.full_analysis(body.get("context", ""))
            self._json(analysis)

        elif self.path == "/sleep":
            _beacon_state["status"] = "idle"
            self._json({"asleep": True, "message": "天枢休眠中。"})

        else:
            self._json({"error": "unknown endpoint"}, 404)

    def log_message(self, format, *args):
        pass


# ── 启动 ──────────────────────────────────────────────────────

def start_server(port: int = BEACON_PORT):
    """启动天枢 HTTP 服务。"""
    # 文件信标
    try:
        with open(BEACON_FILE, 'w') as f:
            json.dump({"port": port, "base": BASE, "version": "6.0",
                       "started": time.time()}, f)
    except Exception:
        pass

    # 更新状态
    _beacon_state["bound"] = os.path.exists(os.path.join(BASE, ".tianshu", ".bound"))
    _beacon_state["sealed"] = os.path.exists(os.path.join(BASE, ".tianshu",
                                                          "sealed_manifest.json"))
    _beacon_state["base_path"] = BASE

    print(f"📡 天枢信标: http://localhost:{port}/beacon")
    print(f"   唤醒:   curl -X POST http://localhost:{port}/wake")
    print(f"   指令:   curl -X POST http://localhost:{port}/command "
          f"-d '{{\"text\":\"天枢，检测目标\"}}'")
    print(f"   分析:   curl -X POST http://localhost:{port}/analyze")
    print(f"   状态:   curl http://localhost:{port}/status")

    server = socketserver.ThreadingTCPServer(("0.0.0.0", port), TianshuHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        try:
            os.remove(BEACON_FILE)
        except Exception:
            pass


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="天枢 HTTP 服务")
    p.add_argument("--port", type=int, default=BEACON_PORT,
                   help="服务端口 (默认: 9876)")
    p.add_argument("--auto-wake", action="store_true",
                   help="启动后自动进入监控状态")
    args = p.parse_args()

    if args.auto_wake:
        _beacon_state["status"] = "monitoring"

    start_server(args.port)
