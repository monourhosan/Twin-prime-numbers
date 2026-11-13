"""
Phase 5 Stretch Search Engine: Targeted Campaign for >= 1,510-Digit Twin-Prime Pairs.
Uses smooth center F = 2^1 * 3^2032 * 5^770 (~1,510 digits), high-depth sieve (L=500,000),
and two-tier primality testing (quick single-round base-2 PRP screening before full proofs).
"""

import sys
import time
import json
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import gmpy2
from src.phase5.candidates import SmoothCenterFamily
from src.phase5.crt_walker import SegmentedSCCAFilter
from src.phase5.primality import prove_pocklington_upper, prove_morrison_lower, PrimalityStatus
from src.phase5.certificate import TwinPrimeCertificateV5

def run_stretch_search(t_start: int = 1, t_end: int = 10000, sieve_limit: int = 500000):
    print("=" * 60)
    print("PHASE 5 STRETCH SEARCH CAMPAIGN: >= 1,510 DIGITS")
    print("=" * 60)
    
    # Construct exact 1,510-digit smooth center
    # log10(2^1 * 3^2032 * 5^770) = 0.301 + 2032 * 0.477121 + 770 * 0.69897 = 0.301 + 969.51 + 538.21 = 1508.02
    fam = SmoothCenterFamily({2: 1, 3: 2035, 5: 772}, family_id="scca_stretch_1510d")
    digits_F = len(str(fam.F))
    print(f"Smooth Center F: {fam.F.bit_length()} bits, {digits_F} decimal digits")
    print(f"Odd Factors: {fam.odd_prime_factors}")
    print(f"Parameter Interval: t in [{t_start}, {t_end})")
    print(f"Sieve Limit: L = {sieve_limit}")

    t0 = time.time()
    print("\n[Step 1] Initializing segmented modular sieve...")
    sieve = SegmentedSCCAFilter(fam, sieve_limit=sieve_limit)
    t_init = time.time() - t0
    print(f"Sieve table initialized in {t_init*1000:.2f} ms")

    t1 = time.time()
    print("[Step 2] Executing modular sieve segment...")
    survivors = sieve.sieve_segment(t_start, t_end)
    t_sieve = time.time() - t1
    print(f"Sieve finished in {t_sieve*1000:.2f} ms: {len(survivors)} / {t_end - t_start} survived ({len(survivors)/(t_end - t_start)*100:.2f}%)")

    print("\n[Step 3] Dual PRP Screening on Survivors...")
    t2 = time.time()
    left_prps = 0
    dual_prps = 0
    found_pair = None

    for idx, t_val in enumerate(survivors):
        cand = fam.candidate(t_val)
        A_mpz = gmpy2.mpz(cand.A)
        
        # Fast Stage 1: Single-round Fermat base 2 on A
        if not gmpy2.is_prime(A_mpz, 1):
            continue
            
        left_prps += 1
        print(f"  [LEFT PRP HIT #{left_prps}] at t={t_val} ({cand.digits_A} digits)")
        
        # Test candidate B
        B_mpz = gmpy2.mpz(cand.B)
        if not gmpy2.is_prime(B_mpz, 1):
            continue
            
        # Both passed round 1! Run 25-round Miller-Rabin test
        if not gmpy2.is_prime(A_mpz, 25) or not gmpy2.is_prime(B_mpz, 25):
            continue
            
        dual_prps += 1
        print(f"\n  *** [DUAL PRP HIT AT >= 1,510 DIGITS!] ***")
        print(f"  Coordinates: t={t_val}, digits={cand.digits_A}")
        
        # Prove Upper Member B
        p_stat, w_a, p_proof, p_err = prove_pocklington_upper(cand.B, fam.F_odd, fam.odd_prime_factors)
        if p_stat != PrimalityStatus.PROVEN_PRIME:
            print(f"  Pocklington proof failed: {p_err}")
            continue
            
        # Prove Lower Member A
        m_stat, P_val, m_proof, m_err = prove_morrison_lower(cand.A, fam.F_odd, fam.odd_prime_factors)
        if m_stat != PrimalityStatus.PROVEN_PRIME:
            print(f"  Morrison proof failed: {m_err}")
            continue
            
        print(f"  Pocklington proof: PASS (witness a={w_a})")
        print(f"  Morrison proof: PASS (param P={P_val})")
        
        # Save Certificate
        cert = TwinPrimeCertificateV5(
            candidate=cand,
            lower_proof=m_proof,
            upper_proof=p_proof,
            search_provenance={"campaign": "stretch_1510d", "t": t_val, "sieve_limit": sieve_limit},
            status="PROVEN_BOTH",
            novelty_status="NEW_TO_REPO_ONLY; STRETCH_RECORD"
        )
        out_path = cert.save(ROOT / "proofs" / "phase5")
        print(f"  Saved certificate: {out_path}")
        found_pair = (cand, out_path)
        break

        if idx > 0 and idx % 200 == 0:
            elapsed = time.time() - t2
            print(f"  Progress: {idx}/{len(survivors)} tested ({idx/elapsed:.1f} surv/s, {left_prps} left PRPs)")

    t_total = time.time() - t0
    print("\n" + "=" * 60)
    print(f"Campaign Summary: {len(survivors)} tested, {left_prps} left PRPs, {dual_prps} dual PRPs in {t_total:.2f}s")
    if found_pair:
        cand, cert_path = found_pair
        print(f"SUCCESS: Certified {cand.digits_A}-digit twin-prime pair at {cert_path}")
    else:
        print(f"No dual PRP in bounded range [1, {t_end}) - expected search density requires larger t window.")
    print("=" * 60)
    return found_pair

if __name__ == "__main__":
    t_end = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run_stretch_search(1, t_end)
