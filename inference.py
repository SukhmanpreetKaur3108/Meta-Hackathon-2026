"""
inference.py — Baseline inference script for LPG Crisis Allocation OpenEnv.

Mandatory environment variables:
  API_BASE_URL   e.g. https://router.huggingface.co/v1
  MODEL_NAME     e.g. meta-llama/Llama-3.3-70B-Instruct
  HF_TOKEN       Your Hugging Face access token (also accepted as API_KEY)

Free alternative (no credits needed):
  API_BASE_URL=https://api.groq.com/openai/v1
  MODEL_NAME=llama-3.3-70b-versatile
  HF_TOKEN=gsk_your_groq_key   (from console.groq.com)

Run:
  python inference.py
"""
from __future__ import annotations

import json
import os
import re
import textwrap
from typing import Any, Dict, List, Optional

# Load .env file if present (pip install python-dotenv)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

from lpg_crisis_env import LPGCrisisEnv, GRADERS
from lpg_crisis_env.graders import THRESHOLDS
from lpg_crisis_env.models import Action, AllocationAction, Observation

# ── Config ─────────────────────────────────────────────────────────────────────
API_BASE_URL: str = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY: str = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or ""
MODEL_NAME: str = os.getenv("MODEL_NAME", "meta-llama/Llama-3.3-70B-Instruct")

TEMPERATURE = 0.1
MAX_TOKENS = 1024

# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = textwrap.dedent("""
You are an AI resource-allocation agent managing LPG cylinder distribution
during a supply crisis in India.

Each day you receive a JSON observation describing district states and available
cylinders. You must decide how many cylinders to allocate to each district.

Rules:
1. Total allocations must NOT exceed cylinders_remaining.
2. Blocked routes (route_blocked: true) CANNOT receive allocations — skip them.
3. Prioritise districts with high vulnerable_households and low current_stock.
4. High black_market_index means leakage — activate emergency protocols for those.
5. Hospital zones and military priority districts must NEVER run out.
6. Allocate ALL available cylinders — do not leave budget unused.

Respond ONLY with valid JSON, no explanation:
{
  "allocations": [
    {"district_id": "D001", "cylinders": 5000, "priority_vulnerable": true},
    ...
  ],
  "activate_emergency": ["D006", "D007"]
}
""").strip()


# ── Smart heuristic fallback (used when LLM fails or quota exhausted) ──────────

def smart_fallback_action(obs: Observation) -> Action:
    """
    Demand-weighted proportional allocation with vulnerability and priority bonuses.
    Much better than equal-split — scores consistently above thresholds.
    """
    eligible = [d for d in obs.districts if not d.route_blocked]
    if not eligible:
        return Action(allocations=[], activate_emergency=[])

    # Weight = demand + 30% bonus for vulnerable households + priority zone boost
    weights = []
    for d in eligible:
        vuln_ratio = d.vulnerable_households / max(d.households, 1)
        priority_boost = 1.5 if (d.hospital_zone or d.military_priority) else 1.0
        w = d.daily_demand * (1.0 + 0.4 * vuln_ratio) * priority_boost
        # Districts with very low stock get extra urgency
        if d.current_stock < d.daily_demand * 0.5:
            w *= 1.3
        weights.append(max(w, 1.0))

    total_w = sum(weights)
    budget = obs.cylinders_remaining
    allocs = []
    used = 0
    for i, (d, w) in enumerate(zip(eligible, weights)):
        if i == len(eligible) - 1:
            cylinders = budget - used  # give remainder to last district
        else:
            cylinders = int(budget * w / total_w)
        cylinders = max(0, cylinders)
        allocs.append(AllocationAction(
            district_id=d.district_id,
            cylinders=cylinders,
            priority_vulnerable=True,
        ))
        used += cylinders

    # Activate emergency for high black-market districts
    emergency = [d.district_id for d in eligible if d.black_market_index > 0.30]

    return Action(allocations=allocs, activate_emergency=emergency)


# ── Prompt builder ─────────────────────────────────────────────────────────────

def obs_to_prompt(obs: Observation, step: int) -> str:
    lines = []
    for d in obs.districts:
        tags = []
        if d.route_blocked:
            tags.append("BLOCKED")
        if d.hospital_zone:
            tags.append("HOSPITAL")
        if d.military_priority:
            tags.append("MILITARY")
        tag_str = f" [{', '.join(tags)}]" if tags else ""
        lines.append(
            f"  {d.district_id} {d.name} ({d.state}){tag_str}: "
            f"stock={d.current_stock}, demand={d.daily_demand}, "
            f"vuln_hh={d.vulnerable_households}, bm={d.black_market_index:.2f}, "
            f"induction={d.induction_adoption_rate:.2f}"
        )

    return (
        f"Step {step} | Day {obs.current_day} | Days left: {obs.days_remaining}\n"
        f"Crisis: {obs.crisis_type.value} | Severity: {obs.crisis_severity}\n"
        f"Budget today: {obs.cylinders_remaining:,} cylinders\n"
        f"Market price: {obs.market_price_multiplier:.2f}x normal\n\n"
        f"Districts:\n" + "\n".join(lines) +
        f"\n\nAllocate up to {obs.cylinders_remaining:,} cylinders total."
    )


# ── JSON parser ────────────────────────────────────────────────────────────────

def parse_action(response_text: str, obs: Observation) -> Action:
    cleaned = re.sub(r"```(?:json)?|```", "", response_text).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return smart_fallback_action(obs)
    try:
        data = json.loads(match.group(0))
        allocs_raw = [AllocationAction(**a) for a in data.get("allocations", [])]
        emergency = data.get("activate_emergency", [])
        # Clamp to budget
        used = 0
        clamped = []
        for a in allocs_raw:
            give = max(0, min(a.cylinders, obs.cylinders_remaining - used))
            clamped.append(AllocationAction(
                district_id=a.district_id,
                cylinders=give,
                priority_vulnerable=a.priority_vulnerable,
            ))
            used += give
        return Action(allocations=clamped, activate_emergency=emergency)
    except Exception:
        return smart_fallback_action(obs)


# ── Verbose per-step printer ───────────────────────────────────────────────────

def print_step_details(obs: Observation, action: Action, reward: float, info: Dict[str, Any]) -> None:
    rb = info["reward_breakdown"]
    alloc_map = {a.district_id: a.cylinders for a in action.allocations}

    # ── Day header ────────────────────────────────────────────────────────────
    print(f"\n  Day {info['day']:>2}  reward={reward:.4f}  coverage={info['avg_coverage']:.1%}"
          f"  allocated={info['cylinders_allocated']:,}")

    # ── Reward breakdown ──────────────────────────────────────────────────────
    print(f"         Coverage:{rb['coverage_score']:.3f}  Equity:{rb['equity_score']:.3f}"
          f"  Vulnerability:{rb['vulnerability_score']:.3f}  "
          f"Efficiency:{rb['efficiency_score']:.3f}  BM-penalty:{rb['black_market_penalty']:.3f}")

    # ── War events ────────────────────────────────────────────────────────────
    blocked = [d.name for d in obs.districts if d.route_blocked]
    if blocked:
        print(f"         [WAR] Routes blocked: {', '.join(blocked)}")

    # ── Priority zone status ──────────────────────────────────────────────────
    priority = [(d, alloc_map.get(d.district_id, 0)) for d in obs.districts
                if d.hospital_zone or d.military_priority]
    if priority:
        zone_status = []
        for d, given in priority:
            zone_type = "H" if d.hospital_zone else "M"
            status = "OK" if given > 0 else "STARVED"
            zone_status.append(f"[{zone_type}]{d.name}({given:,})-{status}")
        print(f"         [PRIORITY] {' | '.join(zone_status)}")

    # ── Black market leakage ──────────────────────────────────────────────────
    total_alloc = info["cylinders_allocated"]
    if total_alloc > 0:
        leakage_est = int(total_alloc * rb["black_market_penalty"])
        if leakage_est > 0:
            print(f"         [BM-LOSS] ~{leakage_est:,} cylinders lost to black market ({rb['black_market_penalty']:.1%})")

    # ── Emergency protocols ───────────────────────────────────────────────────
    if action.activate_emergency:
        names = [d.name for d in obs.districts if d.district_id in action.activate_emergency]
        print(f"         [EMERGENCY] Active in: {', '.join(names)}")

    # ── Top 3 district allocations ────────────────────────────────────────────
    top = sorted(
        [(d, alloc_map.get(d.district_id, 0)) for d in obs.districts if not d.route_blocked],
        key=lambda x: x[1], reverse=True
    )[:3]
    for d, given in top:
        pct = given / d.daily_demand * 100 if d.daily_demand > 0 else 0
        induction_saved = int(d.daily_demand / (1 - d.induction_adoption_rate * 0.5 + 1e-9)
                               * d.induction_adoption_rate * 0.5)
        print(f"         [ALLOC] {d.name:<18} {given:>8,} cyl  "
              f"({pct:.0f}% of demand, induction saves ~{induction_saved:,}/day)")


# ── Episode runner ─────────────────────────────────────────────────────────────

def run_episode(client: Optional[OpenAI], task: str) -> Dict[str, Any]:
    env = LPGCrisisEnv(task=task)
    obs = env.reset()

    # ── Print induction context once at episode start ─────────────────────────
    total_induction_saved = sum(
        int(d.daily_demand / (1 - d.induction_adoption_rate * 0.5 + 1e-9) * d.induction_adoption_rate * 0.5)
        for d in obs.districts
    )
    high_adoption = sorted(obs.districts, key=lambda d: d.induction_adoption_rate, reverse=True)[:3]
    print(f"\n  [INDUCTION] Amazon +30x / Flipkart +4x stove sales surge reduces LPG demand:")
    print(f"     Total demand reduction: ~{total_induction_saved:,} cylinders/day")
    for d in high_adoption:
        saved = int(d.daily_demand / (1 - d.induction_adoption_rate * 0.5 + 1e-9) * d.induction_adoption_rate * 0.5)
        print(f"     {d.name:<20} adoption={d.induction_adoption_rate:.0%}  saves ~{saved:,} cyl/day")

    episode_rewards: List[float] = []
    step = 0
    llm_failures = 0

    while True:
        step += 1
        use_fallback = (client is None or llm_failures >= 3)

        if not use_fallback:
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": obs_to_prompt(obs, step)},
                    ],
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                )
                response_text = completion.choices[0].message.content or ""
                action = parse_action(response_text, obs)
                llm_failures = 0
            except Exception as exc:
                err = str(exc)
                if "402" in err:
                    print(f"\n  [WARN] HF credits exhausted — switching to smart heuristic agent.")
                    llm_failures = 999  # switch permanently
                else:
                    print(f"  [WARN] LLM error: {exc}")
                    llm_failures += 1
                action = smart_fallback_action(obs)
        else:
            action = smart_fallback_action(obs)

        obs, reward, done, info = env.step(action)
        episode_rewards.append(reward)
        print_step_details(obs, action, reward, info)

        if done:
            break

    final_state = env.state()
    grader = GRADERS[task]
    score = grader(env, episode_rewards, final_state)
    return {
        "task": task,
        "score": score,
        "threshold": THRESHOLDS[task],
        "mean_reward": sum(episode_rewards) / len(episode_rewards),
        "steps": step,
        "used_llm": llm_failures < 3,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    if not API_KEY:
        raise EnvironmentError(
            "Set HF_TOKEN or API_KEY in your .env file before running.\n"
            "Free option: get a Groq key at console.groq.com, then set:\n"
            "  API_BASE_URL=https://api.groq.com/openai/v1\n"
            "  MODEL_NAME=llama-3.3-70b-versatile\n"
            "  HF_TOKEN=gsk_your_groq_key"
        )

    client: Optional[OpenAI] = None
    if API_KEY and MODEL_NAME:
        client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    print("=" * 65)
    print("  LPG Crisis Allocation — Baseline Inference")
    print(f"  Model : {MODEL_NAME}")
    print(f"  API   : {API_BASE_URL}")
    print("=" * 65)

    results: List[Dict[str, Any]] = []
    for task in ("easy", "medium", "hard"):
        print(f"\n{'='*65}")
        print(f"  TASK: {task.upper()}")
        print(f"{'='*65}")
        result = run_episode(client, task)
        results.append(result)
        status = "PASS" if result["score"] >= result["threshold"] else "FAIL"
        print(f"\n  --> Final score: {result['score']:.4f}  "
              f"(threshold: {result['threshold']})  [{status}]")
        print(f"     Mean reward: {result['mean_reward']:.4f}  |  Steps: {result['steps']}")

    print(f"\n{'='*65}")
    print("  BASELINE SCORES SUMMARY")
    print(f"  {'Task':<8}  {'Score':>6}  {'Threshold':>9}  {'Result'}")
    print(f"  {'-'*50}")
    for r in results:
        status = "PASS" if r["score"] >= r["threshold"] else "FAIL"
        agent = "LLM" if r["used_llm"] else "Heuristic"
        print(f"  {r['task']:<8}  {r['score']:>6.4f}  {r['threshold']:>9}  {status:<4}  [{agent}]")
    print("=" * 65)


if __name__ == "__main__":
    main()
