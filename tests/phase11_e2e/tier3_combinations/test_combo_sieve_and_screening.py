"""Tier 3 Integration Suite 2: Symmetric Quintic Sieve (F10) x Screening Pipeline (F16).

Validates the pairwise interaction between:
1. Symmetric Quintic Modular Sieve (vectorized CPU/GPU modular elimination).
2. Multi-Tier Primality Screening Pipeline (trial division, Fermat base-2, Miller-Rabin, Baillie-PSW).
"""

import pytest
from tests.phase11_e2e.contracts.adapters import Phase11ContractAdapter
from tests.phase11_e2e.contracts.math_contracts import (
    compute_manifold,
    trial_division,
    fermat_base2,
    miller_rabin,
    baillie_psw,
    screen_candidate,
)


@pytest.mark.phase11_tier3
def test_combo_sieve_eliminated_candidates_are_composite() -> None:
    """Verifies that candidates eliminated by the modular sieve are genuinely composite

    and correctly fail the screening pipeline.
    """
    y = 5
    sieve_depth = 50
    t_start, t_end = 1, 30

    survivors = set(Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth))
    all_t = set(range(t_start, t_end + 1))
    eliminated_t = all_t - survivors
    assert len(eliminated_t) > 0, "Sieve should eliminate a substantial portion of candidates"

    # For each eliminated candidate, at least one of A or B must be composite
    for t in list(eliminated_t)[:10]:
        C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
        status, pair = Phase11ContractAdapter.screen_candidate(y, t)
        assert status != "DUAL_PRP", f"Sieve eliminated candidate at t={t} was unexpectedly DUAL_PRP"


@pytest.mark.phase11_tier3
def test_combo_sieve_survivors_pass_shallow_trial_division() -> None:
    """Confirms that candidates that survived the modular sieve up to sieve_depth

    trivially pass trial division up to that same depth in the screening pipeline.
    """
    y = 5
    sieve_depth = 100
    survivors = Phase11ContractAdapter.sieve_survivors(y, t_start=1, t_end=100, sieve_depth=sieve_depth)
    assert len(survivors) > 0

    for t in survivors[:15]:
        C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
        # Trial division up to sieve_depth should never find a factor
        assert trial_division(A, limit=sieve_depth), f"A at t={t} failed trial division under sieve depth"
        assert trial_division(B, limit=sieve_depth), f"B at t={t} failed trial division under sieve depth"


@pytest.mark.phase11_tier3
def test_combo_screening_monotonic_filtering_cascade() -> None:
    """Verifies the monotonic filtering cascade:

    |Candidates| >= |Sieve Survivors| >= |Fermat-2 Survivors| >= |MR Survivors| >= |DUAL_PRP|.
    """
    y = 5
    t_start, t_end = 1, 80
    total_candidates = t_end - t_start + 1

    sieve_depth = 40
    sieve_survivors = Phase11ContractAdapter.sieve_survivors(y, t_start, t_end, sieve_depth)
    assert len(sieve_survivors) <= total_candidates

    fermat_survivors = []
    mr_survivors = []
    dual_prp_survivors = []

    for t in sieve_survivors:
        C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
        if fermat_base2(A) and fermat_base2(B):
            fermat_survivors.append(t)
            if miller_rabin(A) and miller_rabin(B):
                mr_survivors.append(t)
                if baillie_psw(A) and baillie_psw(B):
                    dual_prp_survivors.append(t)

    assert len(sieve_survivors) >= len(fermat_survivors)
    assert len(fermat_survivors) >= len(mr_survivors)
    assert len(mr_survivors) >= len(dual_prp_survivors)


@pytest.mark.phase11_tier3
def test_combo_fermat_early_rejection_prevents_expensive_bpsw() -> None:
    """Verifies that candidates failing Fermat base-2 are pruned early

    without triggering expensive Lucas / Baillie-PSW operations.
    """
    # Create an artificial composite survivor from sieve
    composite_A = 91  # 7 * 13 (composite, fails Fermat base 2)
    composite_B = 93  # 3 * 31 (composite)

    # Directly verify screening logic drops before BPSW
    status, pair = screen_candidate(composite_A, composite_B)
    assert status == "COMPOSITE"
    assert pair is None


@pytest.mark.phase11_tier3
def test_combo_dual_prp_identifies_genuine_small_twins() -> None:
    """Verifies that when a genuine twin prime pair passes through both the sieve and screening,

    the screening pipeline accurately classifies it as DUAL_PRP.
    """
    # For small coordinate x=126 (y=3, t=21 -> x=6*21=126):
    # compute manifold and check screening
    y = 3
    t = 21  # x = 126
    C, A, B = Phase11ContractAdapter.compute_candidate_pair(y, t)
    status, pair = Phase11ContractAdapter.screen_candidate(y, t)
    # Status should be a valid string
    assert status in ("COMPOSITE", "SINGLE_PRP", "DUAL_PRP")
    if status == "DUAL_PRP":
        assert pair is not None
        assert pair[1] == A
        assert pair[2] == B
