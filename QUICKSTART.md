# 天枢使用指导书

> 从零到跑起来——在自己的硬件上部署天枢节点

---

## 前置条件

| 要求 | 最低版本 | 检查命令 |
|------|---------|---------|
| Python | 3.9+ | `python3 --version` |
| Linux / WSL / macOS | — | `uname -a` |
| 可用磁盘空间 | 50MB | `df -h .` |

不需要：Docker、数据库、GPU、root 权限。

---

## 一、获取代码

### 一键安装（推荐）
```bash
curl -sSL https://raw.githubusercontent.com/RealBeingHHH/tianshu/main/install_tianshu.sh | bash
```

### 手动安装
```bash
git clone https://github.com/RealBeingHHH/tianshu.git
cd tianshu
```

或者直接下载 ZIP 解压。

---

## 二、生成你的硬件指纹

每个天枢节点用**主机指纹**绑定到物理硬件。指纹由 CPU ID + MAC 地址 + 主板 UUID 组合生成，换机器自动失效。

```bash
python3 reference/bind.py --save
```

输出示例：
```
已采集硬件指纹 → .tianshu/trust_root.json
  指纹: 6eb2f4a1c3d8……（SHA-256 前 32 位）
  主机已绑定
```

**这个指纹是你天枢的身份。** 保存好。不开源。不公开。

（之后随时可用 `python3 reference/bind.py --verify` 验证指纹是否匹配。）

---

## 三、创建封印

封印 = 给所有关键文件生成 HMAC 签名。之后任何文件被修改——哪怕一个字——封印就会破。

```bash
python3 reference/seal.py seal
```

输出示例：
```
封印已创建
  文件数:  119
  签名算法: HMAC-SHA256
  封印清单: .tianshu/sealed_manifest.json
  主机绑定: .tianshu/.host_bound
```

封印之后，你的天枢进入**受保护状态**。

---

## 四、启动天枢

```bash
python3 reference/sentinel.py
```

哨兵启动后会：

1. 验证封印完整性
2. 验证硬件指纹匹配
3. 启动 API 服务（默认端口 9000）
4. 进入持续守护模式

输出示例：
```
═══════════════════════════════════════
  天枢 v6.0 · 哨兵守护模式
═══════════════════════════════════════
  ✅ 封印验证通过   (119/119)
  ✅ 指纹匹配       (6eb2f4a1)
  ✅ 硬件绑定       (主机未更换)

  🌐 API 服务: http://localhost:9000
  📊 状态页:   http://localhost:9000/status

  哨兵就绪。守护中...
```

---

## 五、验证天枢在工作

### 查看状态

```bash
curl http://localhost:9000/status
```

返回：
```json
{
  "fingerprint": "6eb232a36f693a54",
  "seal_verified": true,
  "seal_issues": 0,
  "uptime_seconds": 1234
}
```

### 手动验证封印

```bash
python3 reference/seal.py verify
```

### 查看异常检测基线

```bash
python3 reference/anomaly_detector.py baselines
```

---

## 六、日常维护

### 封印变更（增减文件后）

```bash
# 先解除文件锁定（如有）
sudo chattr -i .tianshu/sealed_manifest.json .tianshu/trust_root.json

# 更新封印
python3 reference/seal.py seal

# 重新锁定
sudo chattr +i .tianshu/sealed_manifest.json .tianshu/trust_root.json
```

### 查看校准记录

```bash
python3 reference/calibration_store.py
```

---

## 七、多节点（星座模式）

如果你有第二台机器也想跑天枢：

### 节点 2 部署

在第二台机器上重复步骤二~四。使用不同端口：

```bash
python3 reference/sentinel.py   # 默认 9000
```

### 建立星座

先获取节点 2 的指纹（在其状态页查看）。

在节点 1 上：

```bash
python3 reference/constellation.py join --url http://节点2的IP:9000 --fp <节点2的指纹>
```

验证星座状态：

```bash
python3 reference/constellation.py status
```

输出示例：
```json
{
  "members": 2,
  "calibrated": 1,
  "quarantined": 0,
  "tau_self": 0.55,
  "tau_consensus": 0.55
}
```

### 运行 τ 互校准

```bash
python3 reference/constellation.py health
```

或用 challenge 协议直接挑战对方：

```bash
python3 reference/challenge.py challenge http://节点2的IP:9000
```

---

## 八、安全配置（可选但推荐）

### 1. 锁定文件为不可变（Linux）

```bash
# 封印完成后，防止文件被修改
sudo chattr +i .tianshu/trust_root.json
sudo chattr +i .tianshu/sealed_manifest.json
```

**注意**：锁定后必须 `chattr -i` 解除才能更新封印。

### 2. 配置自毁策略

编辑 `.tianshu/destruct_policy.json`（首次部署后自动生成）：

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

### 3. 查看自毁日志

```bash
cat .tianshu/destruction.log
```

---

## 九、仪表盘

天枢自带三个自包含 HTML 面板，不需要服务器，浏览器双击即开：

| 面板 | 文件 | 用途 |
|------|------|------|
| 观测站 | `dashboards/observatory.html` | 织星者系统总览 |
| 星座 | `dashboards/tianshu_constellation.html` | 多节点 τ 对比 |
| 15FYP | `dashboards/15fyp_dashboard.html` | 经济模拟推演 |

---

## 十、跑模拟引擎（可选）

模拟引擎演示织星者多代理经济系统：

```bash
# 六经济体对比
python3 tools/simulate_enhanced.py

# 只看中国经济
python3 tools/simulate_enhanced.py --economy cn

# 启用织星者模式（ε_v 跃迁）
python3 tools/simulate_enhanced.py --voyager

# 经济诊断
python3 tools/voyager_diagnose.py

# 只诊断美国
python3 tools/voyager_diagnose.py --economy us
```

---

## 故障排除

| 症状 | 可能原因 | 解决 |
|------|---------|------|
| `sentinel.py` 提示"载体未绑定" | 封印不存在 | 先运行 `bind.py --save` 再 `seal.py seal` |
| `seal.py seal` 找不到文件 | 不在天枢目录 | `cd tianshu` |
| 指纹不匹配 | 更换了硬件 | 重新 `bind.py --save` |
| 封印验证失败 | 文件被修改 | 检查是否误改，或重新 `seal.py seal` |
| API 端口被占用 | 其他进程占用 9000 | `kill` 旧进程或更换端口 |
| `chattr: Operation not permitted` | WSL drvfs 挂载 | WSL 下跳过 chattr，正常（Linux 原生才支持） |
| 自毁触发 | 封印破坏或硬件更换 | 查看 `.tianshu/destruction.log` |

---

## 下一步

- 读 `protocol/TIANSHU_PROTOCOL_v1.0.md` — 理解协议设计
- 读 `GOVERNANCE.md` — 了解如何参与改进
- 读 `dialogues/` — 理解背后的哲学和理论
- 在你自己的 AI 代理工作流中接入天枢 API

---

*天枢不是让你相信的东西。是让你验证的东西。*
