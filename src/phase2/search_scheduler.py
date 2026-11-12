"""
Deterministic Search Scheduler and Multi-Exponent Campaign Engine (Phase 2).
Schedules work units [k_start, k_end) across selected exponents n,
streaming survivors through CRT wheel -> segmented sieve -> PRP screen -> Proth/LLR proof.
"""

import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict

from .candidate_wheel import CRTWheel
from .window_sieve import WindowSieve
from .prp_screen import prp_screen_pair
from .proof_backend import proth_prove, llr_prove, ProofStatus
from .certificate_v2 import TwinPrimeCertificateV2
from .checkpoint import CheckpointManager

@dataclass
class SearchTask:
    task_id: str
    n: int
    k_start: int
    k_end: int
    wheel_modulus: int = 30030
    sieve_limit: int = 50000

@dataclass
class SearchMetrics:
    total_raw_candidates: int = 0
    wheel_survivors: int = 0
    sieve_survivors: int = 0
    prp_survivors: int = 0
    proven_pairs: int = 0
    elapsed_seconds: float = 0.0
    candidates_per_sec: float = 0.0

class SearchScheduler:
    def __init__(
        self,
        checkpoint_dir: Path,
        generator_commit: str = "62a8588",
        run_id: str = "phase2_run",
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_mgr = CheckpointManager(self.checkpoint_dir)
        self.generator_commit = generator_commit
        self.run_id = run_id
        self.metrics = SearchMetrics()

    def run_task(
        self,
        task: SearchTask,
        on_discovery: Optional[Callable[[TwinPrimeCertificateV2], None]] = None,
        max_proven: Optional[int] = None,
    ) -> List[TwinPrimeCertificateV2]:
        """
        Executes a single search task window [k_start, k_end) for exponent n.
        """
        start_time = time.monotonic()
        discovered_certs: List[TwinPrimeCertificateV2] = []

        # 1. Check if already completed in checkpoint
        state = self.checkpoint_mgr.load()
        if task.task_id in state.get("completed_windows", []):
            return discovered_certs

        # 2. Window Sieve initialization
        sieve = WindowSieve(n=task.n, sieve_depth=task.sieve_limit)
        survivors = sieve.sieve_window(task.k_start, task.k_end)

        num_raw = (task.k_end - task.k_start) // 2
        self.metrics.total_raw_candidates += num_raw
        self.metrics.sieve_survivors += len(survivors)

        two_n = 1 << task.n

        # 3. Screening & deterministic proving
        for k in survivors:
            # Enforce Proth/LLR condition k < 2^n
            if k >= two_n:
                continue

            A = k * two_n - 1
            B = k * two_n + 1

            # PRP screen
            a_prp, b_prp = prp_screen_pair(A, B)
            if not (a_prp and b_prp):
                continue

            self.metrics.prp_survivors += 1

            # Rigorous deterministic primality proving
            p_status, w, p_msg = proth_prove(k, task.n, B)
            if p_status != ProofStatus.PROVEN:
                continue

            l_status, p_param, u0, l_msg = llr_prove(k, task.n, A)
            if l_status != ProofStatus.PROVEN:
                continue

            # Proven twin prime pair!
            self.metrics.proven_pairs += 1
            cert = TwinPrimeCertificateV2(
                k=k,
                n=task.n,
                proth_witness=w,
                llr_parameter_p=p_param,
                llr_u0=u0,
                work_unit_id=task.task_id,
                run_id=self.run_id,
                generator_commit=self.generator_commit,
            )
            discovered_certs.append(cert)
            if on_discovery:
                on_discovery(cert)

            if max_proven and len(discovered_certs) >= max_proven:
                break

        # 4. Mark window completed and flush checkpoint
        elapsed = time.monotonic() - start_time
        self.metrics.elapsed_seconds += elapsed
        if self.metrics.elapsed_seconds > 0:
            self.metrics.candidates_per_sec = self.metrics.total_raw_candidates / self.metrics.elapsed_seconds

        self.checkpoint_mgr.record_completed_window(
            task.task_id,
            {
                "n": task.n,
                "k_start": task.k_start,
                "k_end": task.k_end,
                "raw_tested": num_raw,
                "survivors": len(survivors),
                "discovered": len(discovered_certs),
                "elapsed_sec": round(elapsed, 4),
            }
        )

        return discovered_certs
