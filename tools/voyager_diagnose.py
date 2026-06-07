#!/usr/bin/env python3
"""
voyager_diagnose.py — 织星者全球经济诊断工具

一键诊断六大经济体，生成对比数据供仪表盘消费。

用法:
    python3 voyager_diagnose.py                    # 诊断所有经济体
    python3 voyager_diagnose.py --economy cn       # 仅诊断中国
    python3 voyager_diagnose.py --years 10         # 10年模拟
"""

import json
import sys
sys.path.insert(0, '/mnt/d/hermes-webui/workspace/evolution')
from simulate_15fyp import PolicyParams, FifteenFYPSimulation

# ═══════════════════════════════════════════════════════════════════════
# 六大经济体参数（基于 2025 年结构特征）
# ═══════════════════════════════════════════════════════════════════════

ECONOMIES = {
    'cn': {
        'name': '中国',
        'flag': '🇨🇳',
        'params': PolicyParams(
            base_verification_efficiency=0.38,
            ai_boost=0.15,
            ai_boost_growth_rate=0.05,
            energy_flow_reduction_rate=0.03,
            green_energy_ratio=0.30,
            carbon_price=80,
            market_connectivity=0.35,
            interregional_trade_cost=0.40,
            tau_uniformity_target=0.10,
            agent_creation_rate=1.0,
            education_investment=0.06,
            external_shock_probability=0.30,
            fundamental_rd_ratio=0.06,
        ),
    },
    'us': {
        'name': '美国',
        'flag': '🇺🇸',
        'params': PolicyParams(
            base_verification_efficiency=0.55,
            ai_boost=0.25,
            ai_boost_growth_rate=0.06,
            energy_flow_reduction_rate=0.01,
            green_energy_ratio=0.22,
            carbon_price=25,
            market_connectivity=0.70,
            interregional_trade_cost=0.15,
            tau_uniformity_target=0.20,
            agent_creation_rate=1.6,
            education_investment=0.08,
            external_shock_probability=0.25,
            fundamental_rd_ratio=0.10,
        ),
    },
    'jp': {
        'name': '日本',
        'flag': '🇯🇵',
        'params': PolicyParams(
            base_verification_efficiency=0.50,
            ai_boost=0.12,
            ai_boost_growth_rate=0.03,
            energy_flow_reduction_rate=0.01,
            green_energy_ratio=0.20,
            carbon_price=30,
            market_connectivity=0.60,
            interregional_trade_cost=0.10,
            tau_uniformity_target=0.05,
            agent_creation_rate=0.7,
            education_investment=0.07,
            external_shock_probability=0.20,
            fundamental_rd_ratio=0.09,
        ),
    },
    'in': {
        'name': '印度',
        'flag': '🇮🇳',
        'params': PolicyParams(
            base_verification_efficiency=0.30,
            ai_boost=0.10,
            ai_boost_growth_rate=0.04,
            energy_flow_reduction_rate=0.01,
            green_energy_ratio=0.25,
            carbon_price=15,
            market_connectivity=0.30,
            interregional_trade_cost=0.45,
            tau_uniformity_target=0.25,
            agent_creation_rate=2.0,
            education_investment=0.04,
            external_shock_probability=0.30,
            fundamental_rd_ratio=0.03,
        ),
    },
    'eu': {
        'name': '欧盟',
        'flag': '🇪🇺',
        'params': PolicyParams(
            base_verification_efficiency=0.50,
            ai_boost=0.12,
            ai_boost_growth_rate=0.04,
            energy_flow_reduction_rate=0.04,
            green_energy_ratio=0.35,
            carbon_price=90,
            market_connectivity=0.65,
            interregional_trade_cost=0.15,
            tau_uniformity_target=0.15,
            agent_creation_rate=0.9,
            education_investment=0.08,
            external_shock_probability=0.20,
            fundamental_rd_ratio=0.08,
        ),
    },
    'dev': {
        'name': '发展中经济体',
        'flag': '🌍',
        'params': PolicyParams(
            base_verification_efficiency=0.22,
            ai_boost=0.05,
            ai_boost_growth_rate=0.02,
            energy_flow_reduction_rate=0.01,
            green_energy_ratio=0.15,
            carbon_price=10,
            market_connectivity=0.20,
            interregional_trade_cost=0.55,
            tau_uniformity_target=0.30,
            agent_creation_rate=2.5,
            education_investment=0.03,
            external_shock_probability=0.40,
            fundamental_rd_ratio=0.02,
        ),
    },
}


def diagnose_all(years=5, agents=50, verbose=True):
    """诊断所有经济体"""
    results = {}

    if verbose:
        print(f"\n{'='*80}")
        print(f"  织星者全球经济诊断 · {len(ECONOMIES)} 经济体 · {agents} Agent × {years} 年")
        print(f"{'='*80}\n")

    for code, econ in ECONOMIES.items():
        if verbose:
            print(f"  {econ['flag']} {econ['name']}...", end=' ', flush=True)

        sim = FifteenFYPSimulation(econ['params'], n_agents=agents)
        sim.run(years=years, verbose=False)

        t0 = sim.history[0]
        t5 = sim.history[-1]

        results[code] = {
            'name': econ['name'],
            'flag': econ['flag'],
            'init': {
                'eta': t0['global_eta'],
                'phi': t0['global_phi'],
                'tau': t0['global_tau'],
                'v': t0['information_velocity_v'],
                'inv_dt': t0['feedback_speed_inv_dt'],
                'eps_v': t0['verification_efficiency_eps_v'],
            },
            'final': {
                'eta': t5['global_eta'],
                'phi': t5['global_phi'],
                'tau': t5['global_tau'],
                'v': t5['information_velocity_v'],
                'inv_dt': t5['feedback_speed_inv_dt'],
                'eps_v': t5['verification_efficiency_eps_v'],
                'phase': t5['phase'],
                'locked': t5['locked_agents'],
                'interventions': t5['total_interventions'],
                'carbon_price': t5['carbon_price'],
            },
            'trajectory': [{
                'year': t['year'],
                'eta': t['global_eta'],
                'phi': t['global_phi'],
                'tau': t['global_tau'],
                'v': t['information_velocity_v'],
                'inv_dt': t['feedback_speed_inv_dt'],
                'phase': t['phase'],
            } for t in sim.history],
        }

        if verbose:
            delta = t5['global_eta'] - t0['global_eta']
            trend = '📈' if delta > 0.05 else ('📉' if delta < -0.05 else '➡')
            print(f"η {t0['global_eta']:.3f}→{t5['global_eta']:.3f} {trend}  {t5['phase']}")

    # 排名
    ranking = sorted(results.items(), key=lambda x: x[1]['final']['eta'], reverse=True)

    if verbose:
        print(f"\n{'='*80}")
        print(f"  全球 η 排名")
        print(f"{'='*80}")
        for i, (code, r) in enumerate(ranking):
            print(f"  {i+1}. {r['flag']} {r['name']}: η={r['final']['eta']:.3f}  φ={r['final']['phi']:.3f}  {r['final']['phase']}")
        print(f"{'='*80}\n")

    return results


def export_comparison(results, filepath='economy_comparison.json'):
    """导出对比数据"""
    with open(filepath, 'w') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return filepath


def main():
    import argparse
    parser = argparse.ArgumentParser(description='织星者全球经济诊断')
    parser.add_argument('--economy', type=str, default=None,
                        choices=list(ECONOMIES.keys()),
                        help='仅诊断指定经济体')
    parser.add_argument('--years', type=int, default=5, help='模拟年数')
    parser.add_argument('--agents', type=int, default=50, help='Agent 数量')
    parser.add_argument('--output', type=str, default='economy_comparison.json')
    parser.add_argument('--quiet', action='store_true')

    args = parser.parse_args()

    if args.economy:
        econ = ECONOMIES[args.economy]
        print(f"\n  {econ['flag']} {econ['name']} 诊断中...\n")
        sim = FifteenFYPSimulation(econ['params'], n_agents=args.agents)
        sim.run(years=args.years, verbose=True)
        results = {args.economy: {
            'name': econ['name'],
            'flag': econ['flag'],
            'final': {
                'eta': sim.history[-1]['global_eta'],
                'phi': sim.history[-1]['global_phi'],
                'phase': sim.history[-1]['phase'],
            },
            'trajectory': sim.history,
        }}
    else:
        results = diagnose_all(years=args.years, agents=args.agents, verbose=not args.quiet)

    path = export_comparison(results, args.output)
    if not args.quiet:
        print(f"  📁 对比数据: {path}")


if __name__ == '__main__':
    main()
