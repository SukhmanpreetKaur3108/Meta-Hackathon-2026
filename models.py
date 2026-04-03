"""
Typed Pydantic models for the LPG Crisis Allocation OpenEnv environment.
Observation, Action, and Reward follow the OpenEnv specification.
"""
from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class CrisisType(str, Enum):
    SUPPLY_SHORTAGE = "supply_shortage"
    WAR = "war"
    NATURAL_DISASTER = "natural_disaster"


class DistrictState(BaseModel):
    district_id: str
    name: str
    state: str
    population: int
    households: int
    vulnerable_households: int          # BPL / elderly / disabled
    current_stock: int                  # cylinders currently on hand
    daily_demand: int                   # adjusted demand (induction-reduced)
    black_market_index: float = Field(ge=0.0, le=1.0)   # leakage risk
    induction_adoption_rate: float = Field(ge=0.0, le=1.0)
    route_blocked: bool = False         # war: supply route cut
    military_priority: bool = False     # war: defense zone
    hospital_zone: bool = False         # critical care zone
    allocated_today: int = 0
    days_without_supply: int = 0
    cumulative_allocated: int = 0


class Observation(BaseModel):
    """Full observable state exposed to the agent each step."""
    districts: List[DistrictState]
    total_available_cylinders: int
    cylinders_remaining: int
    days_remaining: int
    current_day: int
    crisis_type: CrisisType
    crisis_severity: float = Field(ge=0.0, le=1.0)
    market_price_multiplier: float      # >1.0 during shortage
    supply_disruption_prob: float = Field(ge=0.0, le=1.0)
    total_households: int
    covered_households: int


class AllocationAction(BaseModel):
    district_id: str
    cylinders: int = Field(ge=0)
    priority_vulnerable: bool = False   # flag: reserve share for BPL households


class Action(BaseModel):
    """Agent's allocation decision for one day."""
    allocations: List[AllocationAction]
    activate_emergency: List[str] = Field(default_factory=list)  # district_ids


class Reward(BaseModel):
    """Shaped reward breakdown (all components in [0, 1])."""
    coverage_score: float = Field(ge=0.0, le=1.0)
    equity_score: float = Field(ge=0.0, le=1.0)
    vulnerability_score: float = Field(ge=0.0, le=1.0)
    efficiency_score: float = Field(ge=0.0, le=1.0)
    black_market_penalty: float = Field(ge=0.0, le=1.0)
    war_protocol_bonus: float = Field(ge=0.0, le=1.0)
    total: float = Field(ge=0.0, le=1.0)
