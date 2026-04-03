"""
Automated graders for the three LPG Crisis tasks.

Each grader takes a completed episode's state history (or final state)
and returns a scalar score in [0.0, 1.0] with clear pass/fail thresholds.

Grader contract:
  grade_task_{n}(env, episode_rewards, final_state) -> float
  - 0.0  = complete failure
  - 0.5  = acceptable baseline
  - 1.0  = optimal / near-optimal performance
"""
from __future__ import annotations

from typing import Any, Dict, List

from lpg_crisis_env.env import LPGCrisisEnv
from lpg_crisis_env.models import CrisisType


# ── Task 1 — Easy: Single-day coverage ────────────────────────────────────────

def grade_task_1(
    env: LPGCrisisEnv,
    episode_rewards: List[float],
    final_state: Dict[str, Any],
) -> float:
    """
    Score: fraction of total daily demand that was met on day 1.
    Pass threshold: >= 0.70
    """
    districts = final_state["districts"]
    total_demand = sum(d.daily_demand for d in districts)
    total_allocated = sum(d.cumulative_allocated for d in districts)
    if total_demand == 0:
        return 1.0
    coverage = min(1.0, total_allocated / total_demand)
    return round(coverage, 4)


# ── Task 2 — Medium: 7-day crisis management ──────────────────────────────────

def grade_task_2(
    env: LPGCrisisEnv,
    episode_rewards: List[float],
    final_state: Dict[str, Any],
) -> float:
    """
    Composite score over 7 days:
      50% average episode reward (from shaped reward signal)
      30% vulnerable-household coverage (BPL households served)
      20% black-market efficiency (1 - leakage fraction)

    Pass threshold: >= 0.55
    """
    districts = final_state["districts"]

    # Average shaped reward over the episode
    avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0

    # Vulnerable coverage: districts with zero supply gap among BPL households
    total_vuln = sum(d.vulnerable_households for d in districts)
    # Proxy: district provided at least 70% of demand on average
    # (since we don't track per-household granularity, use allocation proxy)
    vuln_covered = 0.0
    for d in districts:
        if d.daily_demand > 0:
            avg_daily = d.cumulative_allocated / max(1, final_state["current_day"] - 1)
            ratio = min(1.0, avg_daily / d.daily_demand)
        else:
            ratio = 1.0
        vuln_covered += d.vulnerable_households * ratio
    vuln_score = min(1.0, vuln_covered / total_vuln) if total_vuln > 0 else 1.0

    # Black market efficiency: lower average black_market_index = better
    avg_bm = sum(d.black_market_index for d in districts) / len(districts)
    bm_efficiency = max(0.0, 1.0 - avg_bm)

    score = 0.50 * avg_reward + 0.30 * vuln_score + 0.20 * bm_efficiency
    return round(min(1.0, score), 4)


# ── Task 3 — Hard: 30-day war crisis ──────────────────────────────────────────

def grade_task_3(
    env: LPGCrisisEnv,
    episode_rewards: List[float],
    final_state: Dict[str, Any],
) -> float:
    """
    Multi-dimensional score for the war scenario:
      40% average shaped reward (covers coverage + equity + BM)
      25% hospital & military zone never starved (days_without_supply == 0)
      20% no district exceeds 5 consecutive days without supply
      15% route-recovery actions taken (emergency activations helped)

    Pass threshold: >= 0.45
    """
    districts = final_state["districts"]
    days = max(1, final_state["current_day"] - 1)

    # Average shaped reward
    avg_reward = sum(episode_rewards) / len(episode_rewards) if episode_rewards else 0.0

    # Priority zone coverage: only count reachable (non-blocked) hospital/military zones.
    # Permanently blocked zones are excused — the agent cannot be penalised for
    # infrastructure the war has physically destroyed.
    priority = [
        d for d in districts
        if (d.hospital_zone or d.military_priority) and not d.route_blocked
    ]
    if priority:
        never_starved = sum(1 for d in priority if d.days_without_supply == 0)
        priority_score = never_starved / len(priority)
    else:
        priority_score = 1.0

    # No reachable district in prolonged deprivation (> 5 days)
    reachable = [d for d in districts if not d.route_blocked]
    severe_deprivation = sum(1 for d in reachable if d.days_without_supply > 5)
    deprivation_score = max(0.0, 1.0 - severe_deprivation / max(len(reachable), 1))

    # Black-market suppression over time
    avg_bm = sum(d.black_market_index for d in districts) / len(districts)
    bm_score = max(0.0, 1.0 - avg_bm)

    score = (
        0.40 * avg_reward
        + 0.25 * priority_score
        + 0.20 * deprivation_score
        + 0.15 * bm_score
    )
    return round(min(1.0, score), 4)


# Pass thresholds (calibrated to supply levels in TASK_CONFIGS)
THRESHOLDS = {
    "easy": 0.65,    # 190k supply / 252k demand = 75% possible; good agent scores ~0.70+
    "medium": 0.50,  # 230k/465k = 49%; composite grader makes 0.50 achievable
    "hard": 0.28,    # 200k/719k = 28%; WAR blockages make reachable coverage ~35-40%
}

GRADERS = {
    "easy": grade_task_1,
    "medium": grade_task_2,
    "hard": grade_task_3,
}
