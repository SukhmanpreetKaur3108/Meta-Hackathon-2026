"""
Shaped reward computation for the LPG Crisis Allocation environment.

Reward components:
  coverage_score       (30%) — fraction of demand met across districts
  equity_score         (20%) — 1 - Gini coefficient of per-district coverage
  vulnerability_score  (25%) — BPL / priority household coverage
  efficiency_score     (10%) — cylinders that actually reach households
  black_market_penalty (10%) — leakage to black market (negative)
  war_protocol_bonus    (5%) — hospital/military zone coverage in WAR mode

Reward provides a dense per-step signal (not just end-of-episode),
rewarding partial progress and penalising clearly harmful allocations.
"""
from __future__ import annotations

from typing import List, Dict, Any

from lpg_crisis_env.models import Action, CrisisType, DistrictState, Reward


def _gini(values: List[float]) -> float:
    """Returns Gini coefficient in [0, 1]. 0 = perfect equality."""
    if not values:
        return 0.0
    total = sum(values)
    if total == 0.0:
        return 0.0
    n = len(values)
    s = sorted(values)
    lorenz = sum((i + 1) * v for i, v in enumerate(s))
    return max(0.0, min(1.0, (2 * lorenz) / (n * total) - (n + 1) / n))


def compute_reward(
    districts: List[DistrictState],
    state: Dict[str, Any],
    action: Action,
) -> Reward:
    if not districts:
        return Reward(
            coverage_score=0.0, equity_score=0.0, vulnerability_score=0.0,
            efficiency_score=0.0, black_market_penalty=0.0, war_protocol_bonus=0.0,
            total=0.0,
        )

    # ── Coverage ──────────────────────────────────────────────────────────────
    coverage_ratios = [
        min(1.0, d.allocated_today / d.daily_demand) if d.daily_demand > 0 else 1.0
        for d in districts
    ]
    coverage_score = sum(coverage_ratios) / len(coverage_ratios)

    # ── Equity ────────────────────────────────────────────────────────────────
    equity_score = 1.0 - _gini(coverage_ratios)

    # ── Vulnerability ─────────────────────────────────────────────────────────
    alloc_map = {a.district_id: a for a in action.allocations}
    total_vulnerable = sum(d.vulnerable_households for d in districts)
    if total_vulnerable > 0:
        vuln_covered = 0.0
        for d in districts:
            cov = min(1.0, d.allocated_today / d.daily_demand) if d.daily_demand > 0 else 1.0
            # priority_vulnerable flag boosts estimated BPL coverage by 50%
            if d.district_id in alloc_map and alloc_map[d.district_id].priority_vulnerable:
                cov = min(1.0, cov * 1.5)
            vuln_covered += d.vulnerable_households * cov
        vulnerability_score = min(1.0, vuln_covered / total_vulnerable)
    else:
        vulnerability_score = 1.0

    # ── Efficiency ────────────────────────────────────────────────────────────
    total_allocated = sum(d.allocated_today for d in districts)
    effective = sum(min(d.allocated_today, d.daily_demand) for d in districts)
    efficiency_score = (effective / total_allocated) if total_allocated > 0 else 1.0
    efficiency_score = min(1.0, efficiency_score)

    # ── Black Market Penalty ──────────────────────────────────────────────────
    leakage = sum(
        d.allocated_today * d.black_market_index * state["crisis_severity"]
        for d in districts
    )
    black_market_penalty = min(1.0, leakage / total_allocated) if total_allocated > 0 else 0.0

    # ── War Protocol Bonus ────────────────────────────────────────────────────
    war_protocol_bonus = 0.0
    if state["crisis_type"] == CrisisType.WAR:
        priority_districts = [d for d in districts if d.hospital_zone or d.military_priority]
        if priority_districts:
            covered_priority = sum(
                1 for d in priority_districts if d.allocated_today > 0
            )
            war_protocol_bonus = covered_priority / len(priority_districts)
        # Penalise prolonged supply gaps (0.5% per district-day without supply)
        penalty = 0.005 * sum(d.days_without_supply for d in districts) / len(districts)
        war_protocol_bonus = max(0.0, war_protocol_bonus - penalty)

    # ── Weighted Total ────────────────────────────────────────────────────────
    total = (
        0.30 * coverage_score
        + 0.20 * equity_score
        + 0.25 * vulnerability_score
        + 0.10 * efficiency_score
        - 0.10 * black_market_penalty
        + 0.05 * war_protocol_bonus
    )
    total = max(0.0, min(1.0, total))

    return Reward(
        coverage_score=coverage_score,
        equity_score=equity_score,
        vulnerability_score=vulnerability_score,
        efficiency_score=efficiency_score,
        black_market_penalty=black_market_penalty,
        war_protocol_bonus=war_protocol_bonus,
        total=total,
    )
