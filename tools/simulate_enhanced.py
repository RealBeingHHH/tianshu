#!/usr/bin/env python3
"""
simulate_enhanced.py — 织星者增强模拟引擎 v3.0

在统计层之上新增：
  体感层：时间贫困·生存安全·日常信任·自主感·代际公平·环境体感
  斩杀线：失业·医疗·信用·社交·心理·制度（6类）
  安全网：低保·医保·保障房·失业保险·菜篮子·法律援助·教育·养老·隐私·心理（10种）
  结构修正：金融化·PPP·制造业占比
  网络效应：恐惧/愤怒/希望传染
  测量悖论：Sinanshu 本身的 η

用法:
    python3 simulate_enhanced.py                     # 六国对比（增强版）
    python3 simulate_enhanced.py --economy cn         # 单一国家详细诊断
    python3 simulate_enhanced.py --economy cn --verbose  # 逐年代理轨迹
"""

import json, math, random, sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════
# 核心方程（从基础引擎继承）
# ═══════════════════════════════════════════════════════════════════════

class VoyagerEquations:
    @staticmethod
    def compute_phi(eta): return max(0.0, min(1.0, 1.0 - eta))
    
    @staticmethod
    def compute_tau(eta, phi, prev_eta, prev_phi):
        d_eta, d_phi = eta - prev_eta, phi - prev_phi
        if abs(d_phi) < 1e-6: return 0.5
        raw = abs(d_eta / d_phi)
        return 0.05 + 0.90 / (1 + math.exp(-5 * (raw - 0.5)))
    
    @staticmethod
    def verification_efficiency(base_eps, ai_boost, carbon_price):
        eps = base_eps + ai_boost * 0.2
        if carbon_price > 50: eps += (carbon_price - 50) / 1000
        return max(0.15, min(0.60, eps))

# ═══════════════════════════════════════════════════════════════════════
# 斩杀线 & 安全网 数据
# ═══════════════════════════════════════════════════════════════════════

EXECUTION_LINES = {
    'unemployment':    {'threshold': 0.35, 'eta_mult': 0.70, 'label': '失业斩杀'},
    'medical_bankrupt':{'threshold': 0.30, 'eta_mult': 0.40, 'label': '医疗斩杀（破产）'},
    'credit_death':    {'threshold': 0.25, 'eta_mult': 0.50, 'label': '信用死亡'},
    'housing_crash':   {'threshold': 0.28, 'eta_mult': 0.45, 'label': '断供法拍'},
    'social_death':    {'threshold': 0.20, 'eta_mult': 0.30, 'label': '社死'},
    'despair':         {'threshold': 0.15, 'eta_mult': 0.05, 'label': '绝望归零'},
    'institutional':   {'threshold': 0.22, 'eta_mult': 0.35, 'label': '制度斩杀（户口/学历/年龄）'},
}

SAFETY_NETS = [
    {'name': '低保',         'tau_protect': 0.08, 'eta_restore': 0.03, 'desc': '基本收入兜底'},
    {'name': '全民医保',     'tau_protect': 0.12, 'eta_restore': 0.05, 'desc': '医疗安全网'},
    {'name': '保障性住房',   'tau_protect': 0.10, 'eta_restore': 0.04, 'desc': '住房缓冲垫'},
    {'name': '失业保险',     'tau_protect': 0.07, 'eta_restore': 0.04, 'desc': '失业过渡期'},
    {'name': '菜篮子工程',   'tau_protect': 0.05, 'eta_restore': 0.02, 'desc': '粮食安全 φ 地板'},
    {'name': '法律援助',     'tau_protect': 0.06, 'eta_restore': 0.03, 'desc': '底层 Sinanshu 接入'},
    {'name': '义务教育',     'tau_protect': 0.05, 'eta_restore': 0.02, 'desc': '代际 τ 维护'},
    {'name': '基础养老金',   'tau_protect': 0.06, 'eta_restore': 0.02, 'desc': '养老恐慌缓冲'},
    {'name': '隐私保护',     'tau_protect': 0.04, 'eta_restore': 0.01, 'desc': '舆论斩杀预防'},
    {'name': '心理援助',     'tau_protect': 0.03, 'eta_restore': 0.02, 'desc': '绝望线缓冲'},
]

# ═══════════════════════════════════════════════════════════════════════
# 体感因子定义
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class BodySenseProfile:
    """国家级别的体感参数"""
    financialization_ratio: float = 0.15   # 金融业占 GDP 比
    ppp_multiplier: float = 1.0            # PPP/名义 GDP 比
    manufacturing_share: float = 0.20      # 制造业占比
    
    # 时间贫困
    annual_work_hours: int = 2000          # 年工作小时
    avg_commute_minutes: int = 45          # 平均通勤分钟
    bureaucracy_wait_index: float = 0.3    # 办事等待指数 0-1
    
    # 生存安全感
    medical_out_of_pocket_ratio: float = 0.15 # 自付医疗比
    house_price_income_ratio: float = 10.0    # 房价收入比
    pension_coverage: float = 0.70           # 养老金覆盖率
    education_cost_burden: float = 0.10       # 教育军备/收入比
    
    # 日常信任（微观 τ）
    food_safety_trust: float = 0.75         # 食品安全信任
    consumer_complaint_resolution: float = 0.50  # 消费投诉解决率
    neighbor_trust: float = 0.60             # 邻里信任
    
    # 自主感
    self_employment_rate: float = 0.15      # 自雇率
    sme_employment_share: float = 0.40      # 中小企业就业比
    digital_platform_choice: float = 0.50   # 数字平台选择权
    
    # 代际公平
    youth_optimism_index: float = 0.55      # 年轻人对未来预期
    
    # 环境体感
    aqi_good_days_ratio: float = 0.75       # 空气质量达标率
    green_space_coverage: float = 0.40      # 绿地覆盖率
    noise_compliance: float = 0.60          # 噪音达标率
    
    # 斩杀线密度
    execution_line_density: float = 0.40    # 综合斩杀线密度 0-1
    
    # 安全网厚度
    safety_net_strength: Dict[str, float] = field(default_factory=dict)
    
    # 结构修正
    eta_structural_correction: float = 0.0  # 金融化/PPP/制造 综合修正
    
    def compute_body_sense_discount(self) -> float:
        """计算体感折扣系数 = 统计 η 打几折"""
        # 时间贫困折扣
        time_poverty = self.annual_work_hours / 8760
        commute_penalty = self.avg_commute_minutes / 180
        bureaucracy_penalty = self.bureaucracy_wait_index
        time_discount = 1.0 - 0.3 * time_poverty - 0.15 * commute_penalty - 0.1 * bureaucracy_penalty
        
        # 生存安全折扣
        medical_discount = 1.0 - 0.2 * self.medical_out_of_pocket_ratio
        housing_discount = 1.0 - 0.15 * min(1.0, self.house_price_income_ratio / 40)
        pension_discount = 0.7 + 0.3 * self.pension_coverage
        edu_discount = 1.0 - 0.15 * self.education_cost_burden
        
        # 微观 τ 折扣
        micro_tau = (self.food_safety_trust + self.consumer_complaint_resolution + self.neighbor_trust) / 3
        
        # 自主感折扣
        autonomy = (self.self_employment_rate + self.sme_employment_share + self.digital_platform_choice) / 3
        autonomy_discount = 0.6 + 0.4 * autonomy
        
        # 代际折扣
        gen_discount = 0.5 + 0.5 * self.youth_optimism_index
        
        # 环境折扣
        env = (self.aqi_good_days_ratio + self.green_space_coverage + self.noise_compliance) / 3
        
        # 斩杀线惩罚
        execution_penalty = 1.0 - 0.25 * self.execution_line_density
        
        # 安全网加成
        net_bonus = 0.0
        for net in SAFETY_NETS:
            if net['name'] in self.safety_net_strength:
                net_bonus += self.safety_net_strength[net['name']] * net['tau_protect']
        net_bonus = min(0.3, net_bonus)
        
        # 综合折扣
        discount = (
            time_discount * 0.20
            + medical_discount * housing_discount * pension_discount * edu_discount * 0.25
            + micro_tau * 0.15
            + autonomy_discount * 0.10
            + gen_discount * 0.10
            + env * 0.05
            + execution_penalty * 0.10
            + net_bonus * 0.05
        )
        return max(0.05, min(0.99, discount))

# ═══════════════════════════════════════════════════════════════════════
# 增强 Agent
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class EnhancedAgent:
    """增强 Agent —— 统计层 + 体感层 + 斩杀线 + 安全网"""
    id: str
    sector: str
    eta: float = 0.5
    phi: float = 0.5
    tau: float = 0.5
    prev_eta: float = 0.5
    prev_phi: float = 0.5
    interventions: int = 0
    locked: bool = False
    activity: str = '●'
    
    # 斩杀线追踪
    crossed_lines: List[str] = field(default_factory=list)
    line_crossed_this_year: bool = False
    
    # 体感层
    eta_perceived: float = 0.5      # 体感 η
    tau_micro: float = 0.5          # 微观信任
    buffer_remaining: float = 1.0   # 剩余缓冲
    
    # 传染
    fear_contagion: float = 0.0     # 恐惧传染系数
    hope_contagion: float = 0.0     # 希望传染系数
    
    # 创伤记忆
    trauma_memory: float = 0.0      # 累积创伤（0-1）
    
    def update(self, new_eta: float, body_profile: 'BodySenseProfile'):
        self.prev_eta, self.prev_phi = self.eta, self.phi
        self.eta = max(0.05, min(0.95, new_eta))
        self.phi = VoyagerEquations.compute_phi(self.eta)
        self.tau = VoyagerEquations.compute_tau(self.eta, self.phi, self.prev_eta, self.prev_phi)
        
        # 斩杀线检查
        self.line_crossed_this_year = False
        for line_name, line_info in EXECUTION_LINES.items():
            if self.eta < line_info['threshold'] and line_name not in self.crossed_lines:
                self.crossed_lines.append(line_name)
                self.line_crossed_this_year = True
                # 触发斩杀效应
                self.eta = max(0.01, self.eta * line_info['eta_mult'])
                self.phi = VoyagerEquations.compute_phi(self.eta)
        
        # 安全网缓冲
        net_bonus = 0.0
        for net in SAFETY_NETS:
            strength = body_profile.safety_net_strength.get(net['name'], 0.0)
            if strength > 0 and self.eta < 0.5:
                net_bonus += strength * net['eta_restore']
        self.eta = min(0.95, self.eta + net_bonus * 0.3)
        
        # 体感 η = 统计 η × 体感折扣 + 结构修正
        discount = body_profile.compute_body_sense_discount()
        structural = body_profile.eta_structural_correction
        self.eta_perceived = max(0.02, self.eta * discount + structural)
        
        # 微观 τ（基于斩杀线触发）
        line_penalty = len(self.crossed_lines) * 0.10
        self.tau_micro = max(0.02, body_profile.food_safety_trust * 0.35 
                             + body_profile.neighbor_trust * 0.35 
                             + body_profile.consumer_complaint_resolution * 0.30 
                             - line_penalty)
        
        # 缓冲剩余
        lowest_line = 1.0
        for line_info in EXECUTION_LINES.values():
            lowest_line = min(lowest_line, line_info['threshold'])
        self.buffer_remaining = max(0.0, (self.eta - lowest_line) / (0.5 - lowest_line))
        
        # 创伤记忆（累积）
        if self.eta < self.prev_eta - 0.05:
            self.trauma_memory = min(1.0, self.trauma_memory + 0.10)
        else:
            self.trauma_memory = max(0.0, self.trauma_memory - 0.02)
    
    def to_dict(self) -> dict:
        return {
            'eta_stat': round(self.eta, 4),
            'eta_perceived': round(self.eta_perceived, 4),
            'phi': round(self.phi, 4),
            'tau': round(self.tau, 4),
            'tau_micro': round(self.tau_micro, 4),
            'buffer': round(self.buffer_remaining, 4),
            'trauma': round(self.trauma_memory, 4),
            'crossed_lines': self.crossed_lines,
            'locked': self.locked,
            'interventions': self.interventions,
            'sector': self.sector,
        }

# ═══════════════════════════════════════════════════════════════════════
# 国家体感配置
# ═══════════════════════════════════════════════════════════════════════

COUNTRY_PROFILES = {
    'cn': BodySenseProfile(
        financialization_ratio=0.14, ppp_multiplier=1.45, manufacturing_share=0.27,
        annual_work_hours=2400, avg_commute_minutes=85, bureaucracy_wait_index=0.45,
        medical_out_of_pocket_ratio=0.17, house_price_income_ratio=35.0,
        pension_coverage=0.70, education_cost_burden=0.15,
        food_safety_trust=0.55, consumer_complaint_resolution=0.40, neighbor_trust=0.45,
        self_employment_rate=0.12, sme_employment_share=0.50, digital_platform_choice=0.30,
        youth_optimism_index=0.40, aqi_good_days_ratio=0.70, green_space_coverage=0.35,
        noise_compliance=0.50, execution_line_density=0.72, eta_structural_correction=0.08,
        safety_net_strength={
            '低保':0.60, '全民医保':0.75, '保障性住房':0.30, '失业保险':0.50,
            '菜篮子工程':0.85, '法律援助':0.35, '义务教育':0.80, '基础养老金':0.60,
            '隐私保护':0.20, '心理援助':0.15,
        }
    ),
    'us': BodySenseProfile(
        financialization_ratio=0.20, ppp_multiplier=1.00, manufacturing_share=0.11,
        annual_work_hours=1800, avg_commute_minutes=52, bureaucracy_wait_index=0.35,
        medical_out_of_pocket_ratio=0.11, house_price_income_ratio=8.0,
        pension_coverage=0.65, education_cost_burden=0.08,
        food_safety_trust=0.80, consumer_complaint_resolution=0.55, neighbor_trust=0.50,
        self_employment_rate=0.10, sme_employment_share=0.45, digital_platform_choice=0.40,
        youth_optimism_index=0.50, aqi_good_days_ratio=0.85, green_space_coverage=0.50,
        noise_compliance=0.70, execution_line_density=0.45, eta_structural_correction=-0.08,
        safety_net_strength={
            '低保':0.35, '全民医保':0.40, '保障性住房':0.15, '失业保险':0.45,
            '菜篮子工程':0.30, '法律援助':0.55, '义务教育':0.70, '基础养老金':0.50,
            '隐私保护':0.50, '心理援助':0.40,
        }
    ),
    'eu': BodySenseProfile(
        financialization_ratio=0.15, ppp_multiplier=1.15, manufacturing_share=0.16,
        annual_work_hours=1600, avg_commute_minutes=40, bureaucracy_wait_index=0.20,
        medical_out_of_pocket_ratio=0.05, house_price_income_ratio=12.0,
        pension_coverage=0.90, education_cost_burden=0.02,
        food_safety_trust=0.85, consumer_complaint_resolution=0.70, neighbor_trust=0.65,
        self_employment_rate=0.10, sme_employment_share=0.55, digital_platform_choice=0.60,
        youth_optimism_index=0.55, aqi_good_days_ratio=0.85, green_space_coverage=0.55,
        noise_compliance=0.75, execution_line_density=0.25, eta_structural_correction=-0.02,
        safety_net_strength={
            '低保':0.85, '全民医保':0.95, '保障性住房':0.65, '失业保险':0.85,
            '菜篮子工程':0.60, '法律援助':0.80, '义务教育':0.95, '基础养老金':0.90,
            '隐私保护':0.85, '心理援助':0.65,
        }
    ),
    'jp': BodySenseProfile(
        financialization_ratio=0.13, ppp_multiplier=1.05, manufacturing_share=0.19,
        annual_work_hours=1700, avg_commute_minutes=60, bureaucracy_wait_index=0.15,
        medical_out_of_pocket_ratio=0.10, house_price_income_ratio=10.0,
        pension_coverage=0.95, education_cost_burden=0.05,
        food_safety_trust=0.90, consumer_complaint_resolution=0.75, neighbor_trust=0.55,
        self_employment_rate=0.08, sme_employment_share=0.60, digital_platform_choice=0.45,
        youth_optimism_index=0.35, aqi_good_days_ratio=0.90, green_space_coverage=0.45,
        noise_compliance=0.80, execution_line_density=0.30, eta_structural_correction=0.02,
        safety_net_strength={
            '低保':0.55, '全民医保':0.90, '保障性住房':0.40, '失业保险':0.55,
            '菜篮子工程':0.50, '法律援助':0.60, '义务教育':0.85, '基础养老金':0.80,
            '隐私保护':0.55, '心理援助':0.35,
        }
    ),
    'in': BodySenseProfile(
        financialization_ratio=0.08, ppp_multiplier=3.50, manufacturing_share=0.14,
        annual_work_hours=2200, avg_commute_minutes=70, bureaucracy_wait_index=0.60,
        medical_out_of_pocket_ratio=0.25, house_price_income_ratio=15.0,
        pension_coverage=0.25, education_cost_burden=0.12,
        food_safety_trust=0.40, consumer_complaint_resolution=0.20, neighbor_trust=0.55,
        self_employment_rate=0.55, sme_employment_share=0.30, digital_platform_choice=0.25,
        youth_optimism_index=0.60, aqi_good_days_ratio=0.40, green_space_coverage=0.15,
        noise_compliance=0.30, execution_line_density=0.75, eta_structural_correction=0.05,
        safety_net_strength={
            '低保':0.20, '全民医保':0.25, '保障性住房':0.05, '失业保险':0.05,
            '菜篮子工程':0.35, '法律援助':0.15, '义务教育':0.50, '基础养老金':0.15,
            '隐私保护':0.10, '心理援助':0.05,
        }
    ),
    'dev': BodySenseProfile(
        financialization_ratio=0.05, ppp_multiplier=2.50, manufacturing_share=0.10,
        annual_work_hours=2300, avg_commute_minutes=80, bureaucracy_wait_index=0.65,
        medical_out_of_pocket_ratio=0.30, house_price_income_ratio=20.0,
        pension_coverage=0.10, education_cost_burden=0.15,
        food_safety_trust=0.30, consumer_complaint_resolution=0.15, neighbor_trust=0.50,
        self_employment_rate=0.60, sme_employment_share=0.20, digital_platform_choice=0.15,
        youth_optimism_index=0.50, aqi_good_days_ratio=0.35, green_space_coverage=0.10,
        noise_compliance=0.25, execution_line_density=0.85, eta_structural_correction=0.03,
        safety_net_strength={
            '低保':0.10, '全民医保':0.10, '保障性住房':0.02, '失业保险':0.02,
            '菜篮子工程':0.20, '法律援助':0.05, '义务教育':0.35, '基础养老金':0.05,
            '隐私保护':0.05, '心理援助':0.02,
        }
    ),
}

COUNTRY_LABELS = {'cn':('🇨🇳','中国'),'us':('🇺🇸','美国'),'eu':('🇪🇺','欧盟'),
                  'jp':('🇯🇵','日本'),'in':('🇮🇳','印度'),'dev':('🌍','发展中')}

# ═══════════════════════════════════════════════════════════════════════
# 增强模拟引擎
# ═══════════════════════════════════════════════════════════════════════

class EnhancedSimulation:
    def __init__(self, country_code: str, n_agents: int = 60, 
                 base_eps: float = 0.38, ai_boost: float = 0.15,
                 ai_growth: float = 0.05, energy_reduction: float = 0.03,
                 carbon_price: float = 80, market_connectivity: float = 0.35,
                 external_shock_prob: float = 0.30, rd_ratio: float = 0.06,
                 education: float = 0.06, trade_cost: float = 0.40,
                 voyager_mode: bool = False, tianshu_api: str = None):
        
        self.country_code = country_code
        self.voyager_mode = voyager_mode
        self.tianshu_tau = None
        self.profile = COUNTRY_PROFILES.get(country_code, COUNTRY_PROFILES['dev'])
        
        # 天枢 API 接入：获取真实 τ 作为信任基准
        if tianshu_api:
            try:
                import urllib.request, json as j
                r = urllib.request.urlopen(f"{tianshu_api}/status", timeout=5)
                data = j.loads(r.read().decode())
                self.tianshu_tau = data.get("tau_value") or (0.55 if data.get("seal_verified") else 0.3)
                # 天枢 τ 增强 ε_v：封印越完整，验证效率越高
                if data.get("seal_verified"):
                    base_eps = min(0.60, base_eps + self.tianshu_tau * 0.15)
            except Exception:
                pass
        
        # 织星者接入：ε_v 跳变 +0.18
        if voyager_mode:
            base_eps = min(0.60, base_eps + 0.18)
            # 体感改善：透明度 → 折扣缩小
            self.profile.execution_line_density *= 0.70  # 实时预警减少斩杀
            self.profile.food_safety_trust = min(0.95, self.profile.food_safety_trust + 0.15)
            self.profile.consumer_complaint_resolution = min(0.90, self.profile.consumer_complaint_resolution + 0.20)
            self.profile.neighbor_trust = min(0.85, self.profile.neighbor_trust + 0.10)
            self.profile.eta_structural_correction += 0.05  # 更高 ε_v → 结构修正加强
            for net in SAFETY_NETS:
                if net['name'] in self.profile.safety_net_strength:
                    self.profile.safety_net_strength[net['name']] = min(0.95, 
                        self.profile.safety_net_strength[net['name']] + 0.10)
        self.n_agents = n_agents
        self.base_eps = base_eps
        self.ai_boost = ai_boost
        self.ai_growth = ai_growth
        self.energy_reduction = energy_reduction
        self.carbon_price = carbon_price
        self.market_connectivity = market_connectivity
        self.external_shock_prob = external_shock_prob
        self.rd_ratio = rd_ratio
        self.education = education
        self.trade_cost = trade_cost
        self.year = 2026
        self.history = []
        
        self.sectors = ['east_coastal','west_inland','northeast','rural',
                        'digital','manufacturing','green_energy','finance']
        self._init_agents()
    
    def _init_agents(self):
        sector_eta = {
            'east_coastal':0.62, 'west_inland':0.40, 'northeast':0.42, 'rural':0.38,
            'digital':0.58, 'manufacturing':0.50, 'green_energy':0.55, 'finance':0.48,
        }
        self.agents = []
        for i in range(self.n_agents):
            sector = self.sectors[i % len(self.sectors)]
            base_eta = sector_eta.get(sector, 0.50) + random.gauss(0, 0.04)
            agent = EnhancedAgent(
                id=f"{sector}_{i}", sector=sector,
                eta=min(0.95, max(0.10, base_eta)),
            )
            agent.phi = VoyagerEquations.compute_phi(agent.eta)
            agent.prev_eta, agent.prev_phi = agent.eta, agent.phi
            self.agents.append(agent)
    
    def step(self):
        eps_v = VoyagerEquations.verification_efficiency(self.base_eps, self.ai_boost, self.carbon_price)
        shocked = random.random() < self.external_shock_prob
        shock = random.uniform(0.03, 0.12) if shocked else 0.0
        
        avg_eta = sum(a.eta for a in self.agents) / len(self.agents)
        policy_response = 0.03 if avg_eta < 0.35 else 0.0
        
        # 计算全局传染系数
        lines_crossed_this_year = sum(1 for a in self.agents if a.line_crossed_this_year)
        fear_contagion_global = min(0.05, lines_crossed_this_year / self.n_agents * 0.15)
        
        for agent in self.agents:
            energy_change = -self.energy_reduction
            verif_effect = (eps_v - 0.35) * 0.3
            
            if agent.sector in ('west_inland','rural','northeast'):
                conn_bonus = (self.market_connectivity - 0.30) * 0.3
            else:
                conn_bonus = (self.market_connectivity - 0.30) * 0.5
            
            carbon_bonus = 0.0
            if agent.sector == 'green_energy':
                carbon_bonus = (self.carbon_price - 50) / 500
            elif agent.sector == 'manufacturing':
                carbon_bonus = -(self.carbon_price - 50) / 800
            
            edu_bonus = (self.education - 0.06) * 0.2
            rd_bonus = (self.rd_ratio - 0.06) * 1.5 * 0.2 if agent.sector in ('digital','green_energy') else 0.0
            
            # 昂萨格耦合（东西部）
            onsager = 0.0
            if agent.sector == 'west_inland':
                east = [a for a in self.agents if a.sector == 'east_coastal']
                if east:
                    avg_e = sum(a.eta for a in east) / len(east)
                    onsager = -0.2 * abs(avg_e - agent.eta) * 0.5
            
            # 结构修正
            structural = self.profile.eta_structural_correction * 0.1
            
            # 斩杀线惩罚（已触发的）
            line_penalty = -0.02 * len(agent.crossed_lines)
            
            # 传染
            contagion = -fear_contagion_global * 0.5
            
            delta_eta = (
                energy_change * 0.05
                + verif_effect * 0.3 + conn_bonus * 0.3 + carbon_bonus * 0.3
                + edu_bonus * 0.2 + rd_bonus * 0.2 + onsager * 0.5
                + shock * 0.8 + policy_response * 0.5 + structural
                + line_penalty + contagion
                + random.gauss(0, 0.008)
            )
            
            new_eta = agent.eta + delta_eta
            agent.update(new_eta, self.profile)
            
            if agent.eta < 0.25:
                agent.interventions += 1
                if agent.interventions > 3: agent.locked = True
                agent.activity = '💤'
            elif agent.eta < 0.4: agent.activity = '○'
            elif agent.eta > 0.6: agent.activity = '🔥'
            else: agent.activity = '●'
        
        self.ai_boost = min(0.5, self.ai_boost * (1 + self.ai_growth * 0.5))
        self.carbon_price = min(300, self.carbon_price * 1.02)
        self.year += 1
    
    def compute_metrics(self) -> dict:
        etas = [a.eta for a in self.agents]
        etas_p = [a.eta_perceived for a in self.agents]
        taus_m = [a.tau_micro for a in self.agents]
        buffers = [a.buffer_remaining for a in self.agents]
        traumas = [a.trauma_memory for a in self.agents]
        total_crossed = sum(len(a.crossed_lines) for a in self.agents)
        agents_crossed = sum(1 for a in self.agents if a.crossed_lines)
        
        eps_v = VoyagerEquations.verification_efficiency(self.base_eps, self.ai_boost, self.carbon_price)
        v = 0.3 + eps_v * 0.5 + self.market_connectivity * 0.2
        inv_dt = 0.2 + eps_v * 0.6 + (1 - self.external_shock_prob) * 0.2
        
        if v > 0.55 and inv_dt > 0.55: phase = 'self_organized_critical'
        elif v < 0.4 and inv_dt < 0.4: phase = 'liquid'
        elif v < 0.45: phase = 'glassy'
        else: phase = 'transition'
        
        # 体感折扣
        discount = self.profile.compute_body_sense_discount()
        
        return {
            'year': self.year - 1,
            'eta_statistical': round(sum(etas)/len(etas), 4),
            'eta_perceived': round(sum(etas_p)/len(etas_p), 4),
            'eta_discount': round(discount, 4),
            'phi': round(1 - sum(etas)/len(etas), 4),
            'tau': round(sum(a.tau for a in self.agents)/len(self.agents), 4),
            'tau_micro': round(sum(taus_m)/len(taus_m), 4),
            'buffer_avg': round(sum(buffers)/len(buffers), 4),
            'trauma_avg': round(sum(traumas)/len(traumas), 4),
            'agents_crossed_lines': agents_crossed,
            'total_lines_crossed': total_crossed,
            'execution_line_density': self.profile.execution_line_density,
            'safety_net_thickness': round(sum(self.profile.safety_net_strength.values())/len(SAFETY_NETS), 4),
            'phase': phase, 'v': round(v,4), 'inv_dt': round(inv_dt,4),
            'eps_v': round(eps_v,4), 'carbon_price': round(self.carbon_price,1),
            'locked_agents': sum(1 for a in self.agents if a.locked),
        }
    
    def run(self, years=5, verbose=True):
        if verbose:
            print(f"\n  {COUNTRY_LABELS[self.country_code][0]} {COUNTRY_LABELS[self.country_code][1]} 增强诊断 · {self.n_agents} Agent · {years} 年")
            print(f"  {'─'*65}")
            print(f"  {'年':<6} {'η统计':<8} {'η体感':<8} {'τ微观':<8} {'斩杀':<6} {'缓冲':<8} {'创伤':<8}")
            print(f"  {'─'*65}")
        
        for _ in range(years):
            self.step()
            m = self.compute_metrics()
            self.history.append(m)
            if verbose:
                print(f"  {m['year']:<6} {m['eta_statistical']:<8.3f} {m['eta_perceived']:<8.3f} {m['tau_micro']:<8.3f} {m['agents_crossed_lines']:<6} {m['buffer_avg']:<8.3f} {m['trauma_avg']:<8.3f}")
        
        if verbose:
            f = self.history[-1]
            print(f"  {'─'*65}")
            print(f"  终态: η统计={f['eta_statistical']:.3f}  η体感={f['eta_perceived']:.3f}  斩杀={f['agents_crossed_lines']}/{self.n_agents}")
            print()
        
        return self.history
    
    def export(self, path='enhanced_results.json'):
        with open(path, 'w') as f:
            json.dump({
                'country': self.country_code,
                'config': {'n_agents':self.n_agents, 'base_eps':self.base_eps},
                'profile': {k:v for k,v in self.profile.__dict__.items() if not k.startswith('_') and not isinstance(v,dict)},
                'profile_safety_nets': self.profile.safety_net_strength,
                'trajectory': self.history,
                'final_state': self.history[-1] if self.history else {},
            }, f, ensure_ascii=False, indent=2)
        return path

# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description='织星者增强模拟引擎 v3.0')
    p.add_argument('--economy', choices=list(COUNTRY_LABELS.keys()), help='单一国家诊断')
    p.add_argument('--years', type=int, default=5)
    p.add_argument('--agents', type=int, default=60)
    p.add_argument('--output', default='enhanced_results.json')
    p.add_argument('--voyager', action='store_true', help='织星者接入模式')
    p.add_argument('--tianshu-api', default=None, help='天枢 API 地址 (如 http://localhost:9000)')
    p.add_argument('--verbose', action='store_true', default=True)
    args = p.parse_args()
    voyager = args.voyager
    tianshu_api = args.tianshu_api
    
    if args.economy:
        profile = COUNTRY_PROFILES[args.economy]
        sim = EnhancedSimulation(args.economy, n_agents=args.agents, voyager_mode=voyager, tianshu_api=tianshu_api)
        sim.run(years=args.years)
        sim.export(args.output)
        print(f"  📁 {args.output}")
    else:
        # 六国对比（含织星者接入对比）
        mode_label = "🛰 织星者接入模式" if voyager else "基线模式"
        print(f"\n{'='*80}")
        print(f"  织星者增强模拟 · 六国对比 · {mode_label}")
        print(f"{'='*80}\n")
        
        # 基线（无织星者）
        baseline = {}
        for code in ['us','cn','eu','jp','in','dev']:
            base_params = {
                'us': (0.55,0.25,0.06,0.01,25,0.70,0.25,0.10,0.08),
                'cn': (0.38,0.15,0.05,0.03,80,0.35,0.30,0.06,0.06),
                'eu': (0.50,0.12,0.04,0.04,90,0.65,0.20,0.08,0.08),
                'jp': (0.50,0.12,0.03,0.01,30,0.60,0.20,0.09,0.07),
                'in': (0.30,0.10,0.04,0.01,15,0.30,0.30,0.03,0.04),
                'dev':(0.22,0.05,0.02,0.01,10,0.20,0.40,0.02,0.03),
            }
            bp = base_params[code]
            sim = EnhancedSimulation(code, n_agents=args.agents,
                base_eps=bp[0], ai_boost=bp[1], ai_growth=bp[2],
                energy_reduction=bp[3], carbon_price=bp[4],
                market_connectivity=bp[5], external_shock_prob=bp[6],
                rd_ratio=bp[7], education=bp[8], voyager_mode=False)
            sim.run(years=args.years, verbose=False)
            baseline[code] = sim.history[-1]
        
        # 织星者模式
        if voyager:
            voyager_results = {}
            for code in ['us','cn','eu','jp','in','dev']:
                base_params = {
                    'us': (0.55,0.25,0.06,0.01,25,0.70,0.25,0.10,0.08),
                    'cn': (0.38,0.15,0.05,0.03,80,0.35,0.30,0.06,0.06),
                    'eu': (0.50,0.12,0.04,0.04,90,0.65,0.20,0.08,0.08),
                    'jp': (0.50,0.12,0.03,0.01,30,0.60,0.20,0.09,0.07),
                    'in': (0.30,0.10,0.04,0.01,15,0.30,0.30,0.03,0.04),
                    'dev':(0.22,0.05,0.02,0.01,10,0.20,0.40,0.02,0.03),
                }
                bp = base_params[code]
                sim = EnhancedSimulation(code, n_agents=args.agents,
                    base_eps=bp[0], ai_boost=bp[1], ai_growth=bp[2],
                    energy_reduction=bp[3], carbon_price=bp[4],
                    market_connectivity=bp[5], external_shock_prob=bp[6],
                    rd_ratio=bp[7], education=bp[8], voyager_mode=True)
                sim.run(years=args.years, verbose=False)
                voyager_results[code] = sim.history[-1]
            
            # 对比表
            ranked = sorted(voyager_results.items(), key=lambda x: x[1]['eta_perceived'], reverse=True)
            print(f"  {'排名':<5} {'国家':<10} {'基线η':<8} {'织星η':<8} {'提升':<8} {'基线体感':<8} {'织星体感':<8} {'斩杀∆':<8}")
            print(f"  {'─'*80}")
            for i, (code, r) in enumerate(ranked):
                b = baseline[code]
                flag, name = COUNTRY_LABELS[code]
                delta_stat = r['eta_statistical'] - b['eta_statistical']
                delta_body = r['eta_perceived'] - b['eta_perceived']
                delta_lines = b['agents_crossed_lines'] - r['agents_crossed_lines']
                print(f"  {i+1:<5} {flag} {name:<7} {b['eta_statistical']:<8.3f} {r['eta_statistical']:<8.3f} +{delta_stat:<7.3f} {b['eta_perceived']:<8.3f} {r['eta_perceived']:<8.3f} {delta_lines:<8}")
            print(f"  {'─'*80}")
            print(f"  💡 织星者接入 = ε_v +0.18 + 斩杀线密度 -30% + 微观信任提升\n")
        else:
            # 仅基线排名
            ranked = sorted(baseline.items(), key=lambda x: x[1]['eta_perceived'], reverse=True)
            print(f"  {'排名':<5} {'国家':<10} {'η统计':<8} {'η体感':<8} {'折扣':<8} {'τ微观':<8} {'斩杀':<8} {'缓冲':<8}")
            print(f"  {'─'*75}")
            for i, (code, r) in enumerate(ranked):
                flag, name = COUNTRY_LABELS[code]
                print(f"  {i+1:<5} {flag} {name:<7} {r['eta_statistical']:<8.3f} {r['eta_perceived']:<8.3f} {r['eta_discount']:<8.3f} {r['tau_micro']:<8.3f} {r['agents_crossed_lines']:<8} {r['buffer_avg']:<8.3f}")
            print(f"  {'─'*75}\n")

if __name__ == '__main__':
    main()
