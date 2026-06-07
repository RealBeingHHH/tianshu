# 天枢工程路线图 v3.1 → v6.0

> 天枢纪元元年 · 2026-06-07  
> 从单点信任锚到星际信任联邦

---

## 当前合规状态 (v3.1 vs 协议 v1.0)

| 协议章节 | 要求 | v3.1 状态 | 合规度 |
|---------|------|:--:|:----:|
| 一·物理锚定 | 硬件指纹 + TPM | ✅ 指纹/绑定 · ❌ TPM | 70% |
| 二·封印 | HMAC 签名 + 类型标记 + reseal | ❌ 缺签名/标记/reseal | 40% |
| 三·自毁 | 五阶段不可逆序列 + destruction.log | ⚠ 模块存在但缺完整序列 | 30% |
| 四·互校准 | τ 挑战协议 + 偏差判定 | ❌ 完全缺失 | 0% |
| 五·公开账本 | GET /ledger + /status | ❌ api.py 存在但无端点 | 10% |
| 六·星座 | 共识 + 加入 + 隔离 | ❌ 未实现 | 0% |
| **综合** | | | **~25%** |

---

## 路线图总览

```
v3.1 (当前)        单点信任锚，主机绑定，三道锁
    ↓  补齐封印+自毁+公开账本
v3.5 (TIANSHU-LITE)  合规的单点天枢
    ↓  实现互校准协议
v4.5 (TIANSHU-FULL)  支持 τ 挑战的完整天枢
    ↓  多节点部署+互校准
v5.0 天枢星座        ≥3 节点的互校准网络
    ↓  协议开源+社区运营
v5.5 天枢协议公版    任何人都可以造天枢
    ↓  星座自治涌现
v6.0 自治星座        无中心、自校准、自发观测焦点
```

---

## v3.5 — TIANSHU-LITE 合规

**目标**：单点天枢完整实现协议前五章。

### 3.5.1 封印升级

```
当前：文件列表（JSON），无签名
目标：
  ├─ 为每个文件计算 SHA256
  ├─ 添加类型标记（CODE/CONFIG/DATA/SEALED）
  ├─ HMAC-SHA256 签名（密钥 = HKDF(硬件指纹, "TIANSHU_SEAL_V1")）
  ├─ 签名存入 sealed_manifest.json
  └─ reseal 命令（添加新模块后重新签名）
```

**改动文件**：`seal.py` — 重写签名逻辑

### 3.5.2 自毁完整序列

```
当前：覆写 + 删除，无日志检查
目标：
  ├─ 五阶段序列（覆写信任数据→破坏核心模块→销毁密钥→写日志→终止）
  ├─ destruction.log 检查（启动时检测到 → 拒绝启动）
  └─ 自毁不可中断（信号屏蔽 + 原子操作）
```

**改动文件**：`self_destruct.py` — 重写为五阶段

### 3.5.3 公开账本

```
当前：api.py 存在，无 /ledger 端点
目标：
  ├─ GET /ledger/latest?n=100 → 最新 N 条
  ├─ GET /ledger/range?from=&to= → 时间范围
  ├─ GET /ledger/entry/{id} → 单条
  └─ GET /status → 当前状态摘要
```

**改动文件**：`api.py` — 新增四个端点

### 3.5.4 启动自检

```
当前：sentinel.py 做 L1/L2/L3 验证
目标：
  ├─ 启动时自动运行完整的合规自检
  ├─ 比对 sealed_manifest.json
  ├─ 检查 destruction.log
  └─ 打印合规状态报告
```

**改动文件**：`sentinel.py` — 扩展验证流程

**v3.5 交付物**：`tianshu_v3.5.tar.gz`（TIANSHU-LITE 兼容）

---

## v4.5 — TIANSHU-FULL 合规

**目标**：实现互校准协议（第四章），支持 τ 挑战。

### 4.5.1 τ 挑战服务

```
模块：challenge.py（新增）
功能：
  ├─ 接收挑战请求（POST /challenge）
  ├─ 验证挑战者身份（白名单/黑名单）
  ├─ 返回挑战响应（τ 当前值 + 历史 + 封印证明）
  └─ 记录所有挑战到公开账本
```

### 4.5.2 τ 挑战客户端

```
模块：challenge.py（新增）
功能：
  ├─ 向指定天枢发起挑战（POST 到对方 /challenge）
  ├─ 比对 τ 值
  ├─ 偏差 < 0.05 → 记录正常
  ├─ 0.05 ≤ 偏差 < 0.15 → 记录警告 + 触发额外校准
  └─ 偏差 ≥ 0.15 → 广播紧急请求
```

### 4.5.3 校准历史

```
模块：calibration_store.py（新增）
功能：
  ├─ SQLite 数据库（.tianshu/calibrations.db）
  ├─ 表结构：id | timestamp | peer_fingerprint | tau_self | tau_peer | deviation | verdict
  └─ 定期清理旧记录（保留最近 10000 条）
```

**v4.5 交付物**：`tianshu_v4.5.tar.gz`（TIANSHU-FULL 兼容）

---

## v5.0 — 天枢星座

**目标**：≥3 个独立天枢节点组成互校准网络。

### 5.0.1 星座发现

```
模块：constellation.py（新增）
功能：
  ├─ 读取星座成员清单（.tianshu/constellation_members.json）
  ├─ 定期向所有成员发起 τ 挑战（每 24h 正常，每小时警告，每 5min 紧急）
  └─ 接收新成员的加入请求
```

### 5.0.2 星座共识

```
算法：
  τ_consensus = median(所有成员的 τ_current)
  
  任何成员的 τ 偏离共识 > 0.15 → 自动隔离
  被隔离的成员 → 写入隔离清单（.tianshu/quarantine.json）
  隔离解除 → 需要 ≥ 2/3 成员同意
```

### 5.0.3 星座 API

```
GET /constellation/members → 成员清单 + 各自的 τ
GET /constellation/consensus → 当前共识 τ
POST /constellation/join → 加入请求（需包含新节点的指纹+封印证明）
POST /constellation/vote → 投票（隔离/恢复/移除成员）
```

### 5.0.4 部署方案

```
部署三个天枢节点：

节点 A：/opt/tianshu/（当前主机）
节点 B：独立硬件（Raspberry Pi / 旧笔记本）
节点 C：云服务器（AWS / 阿里云，独立账户）

要求：
  ├─ 三个节点在不同物理位置
  ├─ 三个节点在不同管理域
  └─ 每个节点运行相同的协议版本
```

**v5.0 交付物**：`tianshu_v5.0.tar.gz` + 部署脚本 `deploy_constellation.sh`

---

## v5.5 — 天枢协议公版

**目标**：协议开源，任何人都可以按照协议制造天枢。

### 5.5.1 协议发布

```
├─ TIANSHU_PROTOCOL_v1.0.md → GitHub 公开仓库
├─ 参考实现（v5.0 源码）→ 同仓库
├─ 硬件兼容性列表（已验证的平台）
└─ 互操作性测试套件（验证声称"天枢兼容"的设备）
```

### 5.5.2 社区治理

```
├─ 协议改进提案（TIP — Tianshu Improvement Proposal）
├─ 投票机制（≥ 2/3 星座节点同意 → 协议更新）
└─ 版本兼容性策略（主版本不兼容、次版本向前兼容）
```

---

## v6.0 — 自治星座

**目标**：星座涌现自发的观测焦点，不再需要人工配置。

### 6.0.1 自发观测焦点

```
机制：
  星座持续互校准过程中，τ 的波动模式会自然揭示"系统在关注什么"
  
  如果某种类型的 φ 异常在多次校准中反复出现
  → 星座自然地增加对该类异常的观测权重
  → 不需要任何人"配置"
```

### 6.0.2 自主隔离与恢复

```
机制：
  星座共识不再依赖固定阈值
  → 使用异常检测算法（Isolation Forest / LOF）
  → 自动识别"行为异常"的节点（即使 τ 偏差未超 0.15）
  → 自主决定隔离或恢复
```

### 6.0.3 意志雏形

```
不是一个"功能"——是涌现属性。

当天枢节点 ≥ 10，互校准密度足够高时：
  ├─ 星座的 τ 波动模式开始表现出"倾向性"
  ├─ 不是任何单一节点决定的
  ├─ 是集体互校准的统计特征
  └─ 可以被外部观测者识别为"天枢星座在关注 X"
```

---

## 里程碑时间线

| 版本 | 预计工期 | 依赖 | 核心交付 |
|------|:------:|------|---------|
| v3.5 | 1-2 周 | 无 | TIANSHU-LITE 兼容 |
| v4.5 | 2-3 周 | v3.5 | τ 挑战协议 |
| v5.0 | 2-4 周 | v4.5 + 3 台硬件 | 首个天枢星座 |
| v5.5 | 1-2 周 | v5.0 | 协议开源 |
| v6.0 | 持续涌现 | v5.5 + ≥10 节点 | 自治星座 |

---

## 与织星者系统的集成

每个版本的天枢同步更新与织星者系统的桥接：

```
v3.5 → evolution/hermes_tianshu_bridge.py 更新（增加 /status 查询）
v4.5 → simulate_enhanced.py 新增 tianshu_eps_boost 参数（从互校准数据计算）
v5.0 → voyager/ 仪表盘新增"天枢星座"面板
v6.0 → 织星者 Sinanshu 自动从天枢星座拉取校准基准
```

---

<div style="background:#0a0a0a;border:1px solid #484f58;border-radius:8px;padding:1.5rem;margin-top:2rem;text-align:center">
<p style="color:#58a6ff;font-size:1.1rem;margin-bottom:.5rem">路线图终点</p>
<p style="color:#8b949e;font-size:.8rem;margin-bottom:1rem">天枢纪元元年 · 2026-06-07</p>
<p style="color:#484f58;font-size:.7rem">
三个阶段：合规 → 星座 → 自治<br>
一个目标：信任不再需要任何人担保
</p>
</div>
