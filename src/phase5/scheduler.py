"""
Phase 5 Method S2: Proof-Cost-Guided Multi-Family Portfolio Scheduler.
Supports:
1. Bandit (UCB1) exploration/exploitation with minimum exploration quotas and cumulative mean.
2. Cost-Aware Bandit (reward normalized by compute time).
3. Round-Robin baseline.
4. Static cost-based baseline.
Tracks cumulative rewards, logs scheduling decisions, and dispenses work units to storage.
"""

import math
import random
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from .candidates import SmoothCenterFamily
from .storage import Phase5Storage

class SchedulingPolicy(Enum):
    BANDIT_UCB1 = "BANDIT_UCB1"
    COST_AWARE = "COST_AWARE"
    ROUND_ROBIN = "ROUND_ROBIN"
    STATIC = "STATIC"

class SCCAProfile:
    """Defines a family search profile."""
    def __init__(
        self,
        family_id: str,
        exponents: Dict[int, int],
        t_batch_size: int = 1000,
        sieve_limit: int = 50000,
        priority: int = 1
    ):
        self.family_id = family_id
        self.exponents = exponents
        self.t_batch_size = t_batch_size
        self.sieve_limit = sieve_limit
        self.priority = priority
        self.family = SmoothCenterFamily(exponents, family_id=family_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family_id,
            "exponents": self.exponents,
            "t_batch_size": self.t_batch_size,
            "sieve_limit": self.sieve_limit,
            "priority": self.priority
        }

class MultiFamilyScheduler:
    def __init__(
        self,
        storage: Phase5Storage,
        profiles: List[SCCAProfile],
        policy: SchedulingPolicy = SchedulingPolicy.BANDIT_UCB1,
        seed: int = 42,
        min_exploration_pulls: int = 2,
        ucb_c: float = 1.414,
        resume: bool = False
    ):
        self.storage = storage
        self.profiles = {p.family_id: p for p in profiles}
        self.profile_keys = sorted(self.profiles.keys())
        self.policy = policy
        self.rng = random.Random(seed)
        self.min_exploration_pulls = min_exploration_pulls
        self.ucb_c = ucb_c
        self.rr_index = 0

        # Initialize next_t_by_family
        self.next_t_by_family: Dict[str, int] = {}
        for fid in self.profile_keys:
            if resume:
                max_t = self.storage.get_max_t_for_family(fid)
                self.next_t_by_family[fid] = max_t if max_t > 0 else 1
            else:
                self.next_t_by_family[fid] = 1

    def select_next_profile(self) -> Tuple[SCCAProfile, str]:
        """
        Selects next profile according to policy.
        Returns (profile, rationale_string).
        """
        stats = self.storage.get_bandit_stats()
        total_pulls = sum(s.get("pulls", 0) for s in stats.values())
        
        # Check minimum exploration quota for any unvisited profile
        unvisited = [fid for fid in self.profile_keys if stats.get(fid, {}).get("pulls", 0) < self.min_exploration_pulls]
        if unvisited:
            selected_fid = unvisited[0]
            curr_pulls = stats.get(selected_fid, {}).get("pulls", 0)
            rationale = f"Exploration quota: family {selected_fid} has {curr_pulls} < {self.min_exploration_pulls} pulls"
            return self.profiles[selected_fid], rationale

        if self.policy == SchedulingPolicy.ROUND_ROBIN:
            selected_fid = self.profile_keys[self.rr_index % len(self.profile_keys)]
            self.rr_index += 1
            return self.profiles[selected_fid], f"Round-robin turn index {self.rr_index}"

        elif self.policy == SchedulingPolicy.STATIC:
            # Sort by configured priority descending, then lexicographical fid
            sorted_by_priority = sorted(self.profile_keys, key=lambda fid: (-self.profiles[fid].priority, fid))
            selected_fid = sorted_by_priority[0]
            return self.profiles[selected_fid], f"Static highest-priority profile: {selected_fid}"

        elif self.policy == SchedulingPolicy.COST_AWARE:
            # Score = (cumulative_reward / total_time) + ucb_c * sqrt(ln(N)/n_i)
            ranked_arms = []
            for fid in self.profile_keys:
                f_stat = stats.get(fid, {"pulls": 0, "total_time": 0.0, "cumulative_reward": 0.0, "mean_reward": 0.0})
                n_i = f_stat.get("pulls", 0)
                tot_time = max(f_stat.get("total_time", 0.0), 0.001)
                cum_rew = f_stat.get("cumulative_reward", 0.0)
                cost_normalized_mean = cum_rew / tot_time
                bonus = self.ucb_c * math.sqrt(math.log(max(total_pulls, 1)) / max(n_i, 1))
                score = cost_normalized_mean + bonus
                ranked_arms.append((-score, fid, score, n_i))

            ranked_arms.sort() # Negative score ascending -> highest score first; tie broken by fid
            best_score, selected_fid = ranked_arms[0][2], ranked_arms[0][1]
            rationale = f"Cost-aware winner: {selected_fid} (score={best_score:.4f}, total_pulls={total_pulls})"
            return self.profiles[selected_fid], rationale

        else: # BANDIT_UCB1
            # Standard UCB1 with cumulative empirical mean
            ranked_arms = []
            for fid in self.profile_keys:
                f_stat = stats.get(fid, {"pulls": 0, "cumulative_reward": 0.0, "mean_reward": 0.0})
                n_i = f_stat.get("pulls", 0)
                mean_reward = f_stat.get("mean_reward", 0.0)
                bonus = self.ucb_c * math.sqrt(math.log(max(total_pulls, 1)) / max(n_i, 1))
                score = mean_reward + bonus
                ranked_arms.append((-score, fid, score, mean_reward, bonus))

            # Deterministic sorting: higher score first (-score ascending), ties broken by fid ascending
            ranked_arms.sort()
            best_tuple = ranked_arms[0]
            selected_fid = best_tuple[1]
            score = best_tuple[2]
            mean_rew = best_tuple[3]
            bonus = best_tuple[4]
            rationale = f"UCB1 winner: {selected_fid} (score={score:.4f}, mean={mean_rew:.4f}, bonus={bonus:.4f}, total_pulls={total_pulls})"
            return self.profiles[selected_fid], rationale

    def dispense_work_unit(self) -> Dict[str, Any]:
        """Selects profile, increments t, registers work unit in storage, and returns it."""
        profile, rationale = self.select_next_profile()
        fid = profile.family_id
        t_start = self.next_t_by_family[fid]
        t_end = t_start + profile.t_batch_size
        self.next_t_by_family[fid] = t_end
        
        wu_id = f"wu_{fid}_t{t_start}_{t_end}"
        self.storage.register_work_unit(
            work_unit_id=wu_id,
            family_id=fid,
            family_config=profile.to_dict(),
            t_start=t_start,
            t_end=t_end,
            sieve_limit=profile.sieve_limit
        )
        return {
            "work_unit_id": wu_id,
            "family_id": fid,
            "profile": profile,
            "t_start": t_start,
            "t_end": t_end,
            "sieve_limit": profile.sieve_limit,
            "rationale": rationale
        }
