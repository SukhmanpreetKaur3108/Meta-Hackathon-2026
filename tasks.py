"""
Task registry for the LPG Crisis Allocation environment.

Each task definition includes:
  - Human-readable description
  - Difficulty level
  - Success threshold (score >= threshold → PASS)
  - Config key mapping to LPGCrisisEnv.TASK_CONFIGS
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class TaskDefinition:
    task_id: str
    name: str
    difficulty: str
    description: str
    success_threshold: float
    config_key: str


TASKS: Dict[str, TaskDefinition] = {
    "task_1": TaskDefinition(
        task_id="task_1",
        name="Emergency Day-1 Allocation",
        difficulty="easy",
        config_key="easy",
        success_threshold=0.70,
        description=(
            "A sudden LPG supply disruption has hit 10 districts. "
            "You receive a one-day cylinder budget (≈50% of normal supply). "
            "Allocate cylinders to maximise household coverage. "
            "No black-market leakage in this scenario — focus purely on "
            "distributing equitably based on population and vulnerability."
        ),
    ),
    "task_2": TaskDefinition(
        task_id="task_2",
        name="7-Day Crisis Management",
        difficulty="medium",
        config_key="medium",
        success_threshold=0.55,
        description=(
            "A prolonged LPG shortage affects 20 districts over 7 days. "
            "Daily supply is only 35% of normal. Black-market diversion is active "
            "(agents can activate emergency protocols to suppress it). "
            "Induction-stove adoption has reduced some districts' demand. "
            "Balance coverage, equity, and vulnerable-household prioritisation "
            "while managing daily replenishment intelligently."
        ),
    ),
    "task_3": TaskDefinition(
        task_id="task_3",
        name="30-Day War Crisis",
        difficulty="hard",
        config_key="hard",
        success_threshold=0.45,
        description=(
            "WAR has disrupted supply chains across all 30 districts for 30 days. "
            "Daily cylinders are 20% of normal. Supply routes are randomly blocked. "
            "Hospital and military zones must be kept operational. "
            "Black-market leakage is high; supply disruptions may halve mid-day stocks. "
            "The agent must dynamically re-route, activate emergency protocols, "
            "and continuously balance civilian needs against strategic priorities."
        ),
    ),
}
