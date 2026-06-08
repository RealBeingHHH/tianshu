# 天枢工具

## simulate_enhanced.py
织星者增强模拟引擎 — 六国经济对比、15年预测。

```bash
python3 tools/simulate_enhanced.py              # 六经济体对比
python3 tools/simulate_enhanced.py --economy cn # 单国模拟
python3 tools/simulate_enhanced.py --voyager    # 接入织星者 ε_v +0.18
```

输出：η统计/η体感/τ微观/斩杀数/缓冲/创伤记忆

## voyager_diagnose.py
全球经济一键诊断 — 6大经济体参数对比。

```bash
python3 tools/voyager_diagnose.py
```

## inline_data.py
仪表盘自包含构建 — 把 fetch() 替换为内嵌数据，脱离服务器也能看。

```bash
python3 tools/inline_data.py dashboard.html
```

输入：含 `fetch('*.json')` 的 HTML → 输出：自包含 HTML（原文件备份为 `.bak`）
