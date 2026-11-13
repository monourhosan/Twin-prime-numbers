"""
Phase 5 Method S2: Proof-Cost-Guided Multi-Family Portfolio Scheduler.
Supports:
1. Bandit (UCB1) exploration/exploitation with minimum exploration quotas.
2. Round-Robin baseline.
3. Static cost-based baseline.
Tracks rewards, logs scheduling decisions, and dispenses work units to storage.
"""

import math
import random
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from .candidates import SmoothCenterFamily
from .storage import Phase5Storage

class SchedulingPolicy(Enum):
    BANDIT_UCB1 = "BANDIT_UCB1"
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
        ucb_c: float = 1.414
    ):
        self.storage = storage
        self.profiles = {p.family_id: p for p in profiles}
        self.profile_keys = sorted(self.profiles.keys())
        self.policy = policy
        self.rng = random.Random(seed)
        self.min_exploration_pulls = min_exploration_pulls
        self.ucb_c = ucb_c
        self.next_t_by_family: Dict[str, int] = {fid: 1 for fid in self.profile_keys}
        self.rr_index = 0

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
            rationale = f"Exploration quota: family {selected_fid} has {stats.get(selected_fid, {}).get('pulls', 0)} < {self.min_exploration_pulls} pulls"
            return self.profiles[selected_fid], rationale

        if self.policy == SchedulingPolicy.ROUND_ROBIN:
            selected_fid = self.profile_keys[self.rr_index % len(self.profile_keys)]
            self.rr_index += 1
            return self.profiles[selected_fid], f"Round-robin turn index {self.rr_index}"

        elif self.policy == SchedulingPolicy.STATIC:
            # Sort by configured priority descending
            sorted_by_priority = sorted(self.profile_keys, key=lambda fid: self.profiles[fid].priority, reverse=True)
            selected_fid = sorted_by_priority[0]
            return self.profiles[selected_fid], f"Static highest-priority profile: {selected_fid}"

        else: # BANDIT_UCB1
            best_fid = None
            best_score = -float('inf')
            
            for fid in self.profile_keys:
                f_stat = stats.get(fid, {"pulls": 0, "total_time": 0.0, "last_reward": 0.0})
                n_i = f_stat["pulls"]
                avg_reward = f_stat["last_reward"]
                bonus = self.ucb_c * math.sqrt(math.log(max(total_pulls, 1)) / max(n_i, 1))
                score = avg_reward + bonus
                if score > best_score:
                    best_score = score
                    best_fid = fid
                    
            selected_fid = best_fid or self.profile_keys[0]
            rationale = f"UCB1 winner: {selected_fid} (score={best_score:.4f}, total_pulls={total_pulls})"
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
