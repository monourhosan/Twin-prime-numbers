"""
Phase 6B Regression and Repair Tests.
Verifies fixes for:
1. Proof backend factor timeout enforcement and bounded factorization.
2. Screening pipeline left-only PRP vs dual-PRP distinction and funnel monotonicity.
3. Campaign early discovery break cursor tracking and gap-free resumption.
4. Sieve survival rate monotonicity across Q limits at large digit scales vs small range saturation.
"""

import time
import tempfile
from pathlib import Path
import pytest

from src.phase6.proof_backend import DeterministicPairProver, is_prime_factor
from src.phase6.screening import CandidateScreener
from src.phase6.coverage import CoverageManager
from src.phase6.segmented import SegmentedCenterSieve
from src.phase6.wheel import CenterWheel
from src.phase6.models import CandidatePair

def test_factor_timeout_and_bounded_factoring():
    """Verify that factor_timeout_sec is strictly enforced without hanging."""
    # A large RSA-like semiprime product of two 100-digit primes
    p = 1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003
    q = 1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000033
    hard_composite = p * q
    
    # Prover with tight 0.5s timeout
    prover = DeterministicPairProver(factor_timeout_sec=0.5)
    t0 = time.perf_counter()
    res = prover.factor_center(hard_composite)
    elapsed = time.perf_counter() - t0
    
    # Must fail safely and cleanly within ~2 seconds
    assert res is None
    assert elapsed < 3.0, f"factor_center exceeded timeout budget: took {elapsed:.2f}s"

def test_is_prime_factor_validation():
    """Verify is_prime_factor deterministically validates primes and rejects composites."""
    assert is_prime_factor(2) is True
    assert is_prime_factor(3) is True
    assert is_prime_factor(1000003) is True
    assert is_prime_factor(1000000007) is True # > 10^7
    assert is_prime_factor(1000000009) is True # > 10^7
    assert is_prime_factor(1000000005) is False # divisible by 5
    assert is_prime_factor(1000000007 * 1000000009) is False

def test_screening_left_prp_independent_from_right():
    """
    Verify that candidates where A is PRP and B is composite are properly marked
    as is_left_prp=True and is_dual_prp=False.
    """
    screener = CandidateScreener(mr_rounds=25)
    
    # m = 8: A = 6*8 - 1 = 47 (prime), B = 6*8 + 1 = 49 (7*7 composite)
    # Small prime screening catches B % 7 == 0
    # Let's test a candidate where A is prime, and B is composite with factors > 257
    # For example: p = 1009 is prime. 6m - 1 = 1009 -> 6m = 1010 -> not div by 6.
    # We can test screen_pair directly:
    A_prime = 1000000007 # prime
    B_comp = 1000000009 * 1000000021 # composite
    dual, is_a, is_b, reason = screener.screen_pair(A_prime, B_comp, order="A_first")
    assert dual is False
    assert is_a is True
    assert is_b is False
    assert reason == "B failed PRP"

    # Also test CandidatePair where A is left PRP, but B is composite
    # For m = 8: A = 47 (prime), B = 49 (7*7 composite)
    res_8 = screener.screen_candidate(8)
    assert res_8.is_left_prp is True
    assert res_8.is_right_prp is False
    assert res_8.is_dual_prp is False
    assert "B divisible by 7" in res_8.rejection_reason

    # Find m where A is prime and B is composite failing Fermat/MR
    found_m = None
    for m in range(2, 200):
        res = screener.screen_candidate(m)
        if res.is_left_prp and not res.is_dual_prp:
            found_m = m
            break
            
    assert found_m is not None, "Should find at least one candidate where A is left PRP but B is composite"
    res = screener.screen_candidate(found_m)
    assert res.is_left_prp is True
    assert res.is_dual_prp is False
    assert res.is_right_prp is False

def test_campaign_early_break_does_not_falsely_complete_segment():
    """Verify that stopping on discovery marks only the exact cursor, not the whole segment."""
    from src.phase6.campaign import GITCSSCampaign
    import shutil
    
    unique_run_id = f"test_early_break_{int(time.time()*1000)}"
    cfg = {
        "campaign_id": "test_early_break_campaign",
        "p_min": "100",
        "p_max": "2000",
        "sieve_limit": 500,
        "segment_size": 200,
        "wheel_primes": [5, 7],
        "time_budget_seconds": 60,
        "historical_inventory": "research/phase5_audit/historical_inventory.json"
    }
    campaign = GITCSSCampaign(config=cfg, run_id=unique_run_id, resume=False)
    campaign.candidates_jsonl = campaign.run_dir / "candidates.jsonl"
    campaign.coverage.manifest_path = campaign.run_dir / "coverage_manifest.json"
    
    created_certs = []
    attest_dir = Path("proofs/phase6/attestations")
    existing_attestations = set(attest_dir.glob("attest_*.json")) if attest_dir.exists() else set()
    try:
        # Run with stop_on_discovery=True
        discoveries = campaign.run_bounded_search(max_segments=1, stop_on_discovery=True)
        assert len(discoveries) == 1
        first_m = discoveries[0]["m"]
        assert first_m == 87 # 521, 523 is proven
        if "certificate_path" in discoveries[0]:
            created_certs.append(Path(discoveries[0]["certificate_path"]))
        
        # Check max completed m recorded
        max_done = campaign.coverage.get_max_completed_m()
        # Must be recorded at first_m (87), NOT seg_end (217)!
        assert max_done == first_m, f"Coverage should record exact cursor {first_m}, got {max_done}"
        
        # Now instantiate a second campaign with resume=True sharing the same DB
        campaign2 = GITCSSCampaign(config=cfg, run_id=unique_run_id, resume=True)
        campaign2.candidates_jsonl = campaign.run_dir / "candidates.jsonl"
        campaign2.coverage = CoverageManager(campaign.db_path, manifest_path=campaign.run_dir / "coverage_manifest.json")
        campaign2.historical_keys.add(f"{discoveries[0]['A']}:{discoveries[0]['B']}")
        
        # Resumed search should pick up from m = 88 and find m = 95 (569, 571)!
        discoveries2 = campaign2.run_bounded_search(max_segments=1, stop_on_discovery=True)
        assert len(discoveries2) == 1
        second_m = discoveries2[0]["m"]
        assert second_m > first_m, f"Resumption should find m > {first_m}, got {second_m}"
        assert second_m == 95
        if "certificate_path" in discoveries2[0]:
            created_certs.append(Path(discoveries2[0]["certificate_path"]))
    finally:
        # Clean up test run directory, certificates, and newly created attestations
        for cp in created_certs:
            if cp.exists():
                try:
                    cp.unlink()
                except Exception:
                    pass
        if attest_dir.exists():
            for att in attest_dir.glob("attest_*.json"):
                if att not in existing_attestations:
                    try:
                        att.unlink()
                    except Exception:
                        pass
        if campaign.run_dir.exists():
            try:
                shutil.rmtree(campaign.run_dir)
            except Exception:
                pass

def test_sieve_survival_monotonicity_at_100d():
    """Verify that increasing sieve limit Q strictly decreases survival fraction at 100 digits."""
    wheel = CenterWheel([5, 7, 11, 13])
    m_100d = 10**99
    window = 50000
    
    survivors = {}
    for Q in [5000, 10000, 50000]:
        sieve = SegmentedCenterSieve(sieve_limit=Q, wheel=wheel)
        surv = sieve.sieve_segment(m_100d, window)
        survivors[Q] = len(surv)
        
    assert survivors[5000] > survivors[10000] > survivors[50000], (
        f"Survival count should strictly decrease with Q: {survivors}"
    )

def test_sieve_small_range_saturation_mechanism():
    """
    Verify the mathematical explanation for the benchmark anomaly:
    For m=10^6, sqrt(6m) ~ 2450. Any Q >= 2450 eliminates all composite numbers,
    so survivor counts for Q=5000 and Q=100000 are identical.
    """
    wheel = CenterWheel([5, 7, 11, 13])
    m_1m = 1000000
    window = 100000
    
    sieve_5k = SegmentedCenterSieve(sieve_limit=5000, wheel=wheel)
    surv_5k = sieve_5k.sieve_segment(m_1m, window)
    
    sieve_100k = SegmentedCenterSieve(sieve_limit=100000, wheel=wheel)
    surv_100k = sieve_100k.sieve_segment(m_1m, window)
    
    # Identical because all composites were eliminated at Q=2450
    assert len(surv_5k) == len(surv_100k), (
        f"At m=1M, Q=5k ({len(surv_5k)}) and Q=100k ({len(surv_100k)}) must match due to sqrt(N) bound"
    )
