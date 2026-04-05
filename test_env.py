"""
Tests for LPGCrisisEnv — validates OpenEnv interface compliance.
Run: pytest tests/
"""
import pytest

from lpg_crisis_env import LPGCrisisEnv, Action, AllocationAction, GRADERS
from lpg_crisis_env.models import Observation, Reward, CrisisType


@pytest.fixture
def easy_env():
    return LPGCrisisEnv(task="easy", seed=0)


@pytest.fixture
def medium_env():
    return LPGCrisisEnv(task="medium", seed=0)


@pytest.fixture
def hard_env():
    return LPGCrisisEnv(task="hard", seed=0)


# ── Interface compliance ───────────────────────────────────────────────────────

class TestOpenEnvInterface:
    def test_reset_returns_observation(self, easy_env):
        obs = easy_env.reset()
        assert isinstance(obs, Observation)

    def test_step_returns_tuple(self, easy_env):
        obs = easy_env.reset()
        action = Action(allocations=[], activate_emergency=[])
        result = easy_env.step(action)
        assert len(result) == 4
        obs2, reward, done, info = result
        assert isinstance(obs2, Observation)
        assert isinstance(reward, float)
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    def test_state_returns_dict(self, easy_env):
        easy_env.reset()
        s = easy_env.state()
        assert isinstance(s, dict)
        assert "districts" in s
        assert "cylinders_remaining" in s

    def test_reward_in_range(self, easy_env):
        easy_env.reset()
        _, reward, _, _ = easy_env.step(Action(allocations=[]))
        assert 0.0 <= reward <= 1.0

    def test_step_raises_before_reset(self, easy_env):
        with pytest.raises(RuntimeError, match="reset"):
            easy_env.step(Action(allocations=[]))

    def test_step_raises_after_done(self, easy_env):
        easy_env.reset()
        # Easy task is 1 day
        _, _, done, _ = easy_env.step(Action(allocations=[]))
        assert done
        with pytest.raises(RuntimeError, match="done"):
            easy_env.step(Action(allocations=[]))


# ── Observation shape ─────────────────────────────────────────────────────────

class TestObservation:
    def test_easy_has_10_districts(self, easy_env):
        obs = easy_env.reset()
        assert len(obs.districts) == 10

    def test_medium_has_20_districts(self, medium_env):
        obs = medium_env.reset()
        assert len(obs.districts) == 20

    def test_hard_has_30_districts(self, hard_env):
        obs = hard_env.reset()
        assert len(obs.districts) == 30

    def test_crisis_type(self, hard_env):
        obs = hard_env.reset()
        assert obs.crisis_type == CrisisType.WAR

    def test_cylinders_remaining_positive(self, easy_env):
        obs = easy_env.reset()
        assert obs.cylinders_remaining > 0


# ── Allocation logic ──────────────────────────────────────────────────────────

class TestAllocation:
    def test_over_allocation_is_clamped(self, easy_env):
        obs = easy_env.reset()
        # Try to allocate 10x the budget to one district
        big_action = Action(allocations=[
            AllocationAction(
                district_id=obs.districts[0].district_id,
                cylinders=obs.cylinders_remaining * 10,
            )
        ])
        _, reward, _, info = easy_env.step(big_action)
        assert info["cylinders_allocated"] <= obs.cylinders_remaining

    def test_blocked_route_skipped(self, hard_env):
        obs = hard_env.reset()
        # Force a district to be blocked and try to allocate to it
        hard_env._state["districts"][0].route_blocked = True
        blocked_id = hard_env._state["districts"][0].district_id
        action = Action(allocations=[
            AllocationAction(district_id=blocked_id, cylinders=1000)
        ])
        _, _, _, info = hard_env.step(action)
        # Blocked district should not have received anything
        d = next(
            d for d in hard_env._state["districts"] if d.district_id == blocked_id
        )
        assert d.allocated_today == 0

    def test_emergency_reduces_bm_index(self, medium_env):
        obs = medium_env.reset()
        target = obs.districts[0].district_id
        original_bm = medium_env._state["districts"][0].black_market_index
        action = Action(
            allocations=[AllocationAction(district_id=target, cylinders=1000)],
            activate_emergency=[target],
        )
        medium_env.step(action)
        new_bm = medium_env._state["districts"][0].black_market_index
        assert new_bm < original_bm


# ── Multi-step episode ────────────────────────────────────────────────────────

class TestEpisode:
    def _run_full_episode(self, env: LPGCrisisEnv):
        obs = env.reset()
        rewards = []
        done = False
        while not done:
            # Simple heuristic: split cylinders proportional to demand
            total_demand = sum(d.daily_demand for d in obs.districts if not d.route_blocked)
            allocs = []
            for d in obs.districts:
                if d.route_blocked or total_demand == 0:
                    continue
                share = int(obs.cylinders_remaining * d.daily_demand / total_demand)
                allocs.append(AllocationAction(district_id=d.district_id, cylinders=share))
            obs, reward, done, _ = env.step(Action(allocations=allocs))
            rewards.append(reward)
        return rewards, env.state()

    def test_easy_completes_in_1_step(self, easy_env):
        rewards, _ = self._run_full_episode(easy_env)
        assert len(rewards) == 1

    def test_medium_completes_in_7_steps(self, medium_env):
        rewards, _ = self._run_full_episode(medium_env)
        assert len(rewards) == 7

    def test_hard_completes_in_30_steps(self, hard_env):
        rewards, _ = self._run_full_episode(hard_env)
        assert len(rewards) == 30

    def test_graders_return_float_in_range(self, easy_env, medium_env, hard_env):
        for task, env in [("easy", easy_env), ("medium", medium_env), ("hard", hard_env)]:
            rewards, final_state = self._run_full_episode(env)
            score = GRADERS[task](env, rewards, final_state)
            assert 0.0 <= score <= 1.0, f"Task {task} grader out of range: {score}"
