"""
LPGCrisisEnv — OpenEnv-compliant reinforcement-learning environment.

Simulates a district-level LPG cylinder allocation problem during
supply crises: shortage, war, or natural disaster.

Interface (OpenEnv spec):
  reset()         → Observation
  step(action)    → (Observation, float, bool, dict)
  state()         → dict
"""
from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional, Tuple

from lpg_crisis_env.data.districts import DISTRICTS_DATA
from lpg_crisis_env.models import (
    Action,
    AllocationAction,
    CrisisType,
    DistrictState,
    Observation,
    Reward,
)
from lpg_crisis_env.reward import compute_reward


class LPGCrisisEnv:
    """
    LPG Supply Crisis Allocation Environment.

    Three built-in task difficulties:
      easy   — 1 day,  10 districts, pure shortage, no black market
      medium — 7 days, 20 districts, shortage + black market
      hard   — 30 days, 30 districts, WAR crisis, route blockages,
                supply disruption, dynamic demand
    """

    TASK_CONFIGS: Dict[str, Dict[str, Any]] = {
        "easy": {
            "days": 1,
            "num_districts": 10,
            # 10-district adjusted demand ≈ 252,000 → 190,000 = 75% supply
            # Achievable threshold: agent scoring ≥0.70 with good allocation
            "daily_cylinders": 190_000,
            "crisis_type": CrisisType.SUPPLY_SHORTAGE,
            "crisis_severity": 0.30,
            "black_market": False,
            "supply_disruption": False,
        },
        "medium": {
            "days": 7,
            "num_districts": 20,
            # 20-district adjusted demand ≈ 465,000 → 230,000 = 49% supply
            "daily_cylinders": 230_000,
            "crisis_type": CrisisType.SUPPLY_SHORTAGE,
            "crisis_severity": 0.60,
            "black_market": True,
            "supply_disruption": False,
        },
        "hard": {
            "days": 30,
            "num_districts": 30,
            # 30-district adjusted demand ≈ 719,000 → 200,000 = 28% supply
            # WAR scenario: severe shortage + blockages + disruptions
            "daily_cylinders": 200_000,
            "crisis_type": CrisisType.WAR,
            "crisis_severity": 0.90,
            "black_market": True,
            "supply_disruption": True,
        },
    }

    def __init__(self, task: str = "medium", seed: Optional[int] = 42) -> None:
        if task not in self.TASK_CONFIGS:
            raise ValueError(f"task must be one of {list(self.TASK_CONFIGS)}")
        self.task = task
        self.config = self.TASK_CONFIGS[task]
        self.seed = seed
        self._rng = random.Random(seed)
        self._state: Optional[Dict[str, Any]] = None

    # ── OpenEnv interface ─────────────────────────────────────────────────────

    def reset(self) -> Observation:
        """Reset to initial state and return the first observation."""
        cfg = self.config
        self._rng = random.Random(self.seed)

        raw = DISTRICTS_DATA[: cfg["num_districts"]]
        districts: List[DistrictState] = []
        for d in raw:
            # Reduce demand proportional to induction-stove adoption
            adjusted_demand = int(
                d["daily_demand"] * (1.0 - d["induction_adoption_rate"] * 0.5)
            )
            districts.append(
                DistrictState(
                    district_id=d["district_id"],
                    name=d["name"],
                    state=d["state"],
                    population=d["population"],
                    households=d["households"],
                    vulnerable_households=d["vulnerable_households"],
                    current_stock=adjusted_demand * 2,  # 2-day buffer at start
                    daily_demand=adjusted_demand,
                    black_market_index=d["black_market_index"] if cfg["black_market"] else 0.0,
                    induction_adoption_rate=d["induction_adoption_rate"],
                    route_blocked=False,
                    military_priority=d.get("military_priority", False),
                    hospital_zone=d.get("hospital_zone", False),
                )
            )

        # WAR: randomly block ~20% of supply routes at episode start
        if cfg["crisis_type"] == CrisisType.WAR:
            for d in districts:
                if self._rng.random() < 0.20:
                    d.route_blocked = True

        self._state = {
            "districts": districts,
            "cylinders_remaining": cfg["daily_cylinders"],
            "current_day": 1,
            "days_remaining": cfg["days"],
            "crisis_type": cfg["crisis_type"],
            "crisis_severity": cfg["crisis_severity"],
            "market_price_multiplier": 1.0 + cfg["crisis_severity"],
            "supply_disruption_prob": 0.25 if cfg["supply_disruption"] else 0.0,
            "done": False,
            "episode_rewards": [],
        }
        return self._build_obs()

    def step(self, action: Action) -> Tuple[Observation, float, bool, Dict[str, Any]]:
        """
        Execute one allocation day.

        Returns:
            observation  — updated state after the step
            reward       — shaped scalar reward in [0, 1]
            done         — True when the episode has ended
            info         — reward breakdown + diagnostics
        """
        if self._state is None:
            raise RuntimeError("Call reset() before step().")
        if self._state["done"]:
            raise RuntimeError("Episode is done. Call reset() to start a new one.")

        s = self._state
        district_map: Dict[str, DistrictState] = {d.district_id: d for d in s["districts"]}
        emergency_set = set(action.activate_emergency)

        # Reset daily counters
        for d in s["districts"]:
            d.allocated_today = 0

        # ── Apply allocations ────────────────────────────────────────────────
        budget_used = 0
        for alloc in action.allocations:
            d = district_map.get(alloc.district_id)
            if d is None or d.route_blocked:
                continue  # skip unknown or blocked districts

            cylinders = max(
                0, min(alloc.cylinders, s["cylinders_remaining"] - budget_used)
            )
            # Black-market leakage: a fraction of delivered cylinders is diverted
            leakage = int(cylinders * d.black_market_index * s["crisis_severity"])
            effective = cylinders - leakage

            d.allocated_today = cylinders
            d.current_stock += effective
            d.cumulative_allocated += cylinders
            budget_used += cylinders

            # Emergency protocol: gradually reduces black market index
            if d.district_id in emergency_set:
                d.black_market_index = max(0.0, d.black_market_index - 0.05)

        s["cylinders_remaining"] -= budget_used

        # ── Daily consumption ────────────────────────────────────────────────
        for d in s["districts"]:
            consumed = min(d.current_stock, d.daily_demand)
            d.current_stock -= consumed
            if consumed < d.daily_demand * 0.5:
                d.days_without_supply += 1
            else:
                d.days_without_supply = max(0, d.days_without_supply - 1)

        # ── WAR dynamics: route changes ───────────────────────────────────────
        if s["crisis_type"] == CrisisType.WAR:
            for d in s["districts"]:
                if not d.route_blocked and self._rng.random() < 0.04:
                    d.route_blocked = True
                elif d.route_blocked and self._rng.random() < 0.10:
                    d.route_blocked = False  # route restored

        # ── Supply disruption (WAR / disaster scenarios) ──────────────────────
        if self._rng.random() < s["supply_disruption_prob"]:
            disruption_factor = self._rng.uniform(0.3, 0.7)
            s["cylinders_remaining"] = int(s["cylinders_remaining"] * disruption_factor)

        # ── Advance day & replenish ───────────────────────────────────────────
        s["current_day"] += 1
        s["days_remaining"] -= 1
        done = s["days_remaining"] <= 0
        s["done"] = done

        if not done:
            s["cylinders_remaining"] += self.config["daily_cylinders"]

        # ── Update market price (tighter supply → higher multiplier) ──────────
        avg_cov = sum(
            min(d.allocated_today, d.daily_demand) / d.daily_demand if d.daily_demand > 0 else 1.0
            for d in s["districts"]
        ) / len(s["districts"])
        s["market_price_multiplier"] = 1.0 + s["crisis_severity"] * (1.0 - avg_cov)

        # ── Reward ────────────────────────────────────────────────────────────
        reward_obj: Reward = compute_reward(s["districts"], s, action)
        s["episode_rewards"].append(reward_obj.total)

        info = {
            "reward_breakdown": reward_obj.model_dump(),
            "cylinders_allocated": budget_used,
            "day": s["current_day"] - 1,
            "avg_coverage": avg_cov,
            "episode_mean_reward": sum(s["episode_rewards"]) / len(s["episode_rewards"]),
        }

        return self._build_obs(), reward_obj.total, done, info

    def state(self) -> Dict[str, Any]:
        """Return a deep copy of the current raw state."""
        if self._state is None:
            raise RuntimeError("Call reset() first.")
        return copy.deepcopy(self._state)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _build_obs(self) -> Observation:
        s = self._state
        total_hh = sum(d.households for d in s["districts"])
        covered_hh = sum(
            d.households for d in s["districts"] if d.current_stock > 0
        )
        return Observation(
            districts=copy.deepcopy(s["districts"]),
            total_available_cylinders=self.config["daily_cylinders"],
            cylinders_remaining=s["cylinders_remaining"],
            days_remaining=s["days_remaining"],
            current_day=s["current_day"],
            crisis_type=s["crisis_type"],
            crisis_severity=s["crisis_severity"],
            market_price_multiplier=s["market_price_multiplier"],
            supply_disruption_prob=s["supply_disruption_prob"],
            total_households=total_hh,
            covered_households=covered_hh,
        )
