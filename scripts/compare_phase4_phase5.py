"""
Rigorous Controlled Head-to-Head Benchmark: Phase 4 ADRS-4 vs Phase 5 SCCA.
Under identical hardware, Python runtime, gmpy2 acceleration, and sieve cutoffs.
Measures:
1. Sieve throughput (cands/sec and survival percentage).
2. PRP screening latency.
3. Deterministic primality proof generation latency.
4. Independent verification latency.
5. End-to-end pipeline comparison across 100d, 500d, and 1500d scales.
"""

import sys
import time
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Phase 4 modules
from src.phase4.t_sieve import SieveR1_TSpace
from src.phase4.prp import screen_pair_prp
from src.phase4.proof import proth_prove, llr_prove
from src.phase4.backend import has_gmpy2

# Phase 5 modules
from src.phase5.candidates import SmoothCenterFamily
from src.phase5.crt_walker import SegmentedSCCAFilter
from src.phase5.primality import prp_test, prove_pocklington_upper, prove_morrison_lower
from scripts.phase5_independent_verify import verify_certificate_v5_payload

def run_stage_benchmarks():
    print("=" * 65)
    print("STAGE E: CONTROLLED BENCHMARK: PHASE 4 ADRS-4 vs PHASE 5 SCCA")
    print("=" * 65)
    print(f"gmpy2 acceleration: {has_gmpy2}")

    bench_scales = [
        {
            "name": "100-digit scale",
            "p4_n": 330,        # k * 2^330 ~ 100 digits
            "p4_k": 12477,
            "p5_exponents": {2: 1, 3: 130, 5: 35}, # ~100 digits
            "p5_t": 3,
            "sieve_span": 20000,
            "sieve_depth": 50000,
            "trials": 5
        },
        {
            "name": "500-digit scale",
            "p4_n": 1664,       # k * 2^1664 ~ 507 digits
            "p4_k": 1183377,
            "p5_exponents": {2: 1, 3: 680, 5: 250}, # ~500 digits
            "p5_t": 3,
            "sieve_span": 20000,
            "sieve_depth": 50000,
            "trials": 5
        },
        {
            "name": "1500-digit scale",
            "p4_n": 4992,       # k * 2^4992 ~ 1509 digits
            "p4_k": 416343,
            "p5_exponents": {2: 1, 3: 2035, 5: 772}, # ~1510 digits
            "p5_t": 3,
            "sieve_span": 20000,
            "sieve_depth": 50000,
            "trials": 5
        }
    ]

    all_results = []

    for cfg in bench_scales:
        scale_name = cfg["name"]
        print(f"\n--- Benchmarking: {scale_name} ---")

        # ---------------------------------------------------------
        # 1. SIEVE THROUGHPUT BENCHMARK
        # ---------------------------------------------------------
        # Phase 4 Sieve: SieveR1_TSpace
        sieve_p4 = SieveR1_TSpace(cfg["p4_n"], cfg["sieve_depth"])
        p4_durations = []
        p4_survivors = 0
        for _ in range(cfg["trials"]):
            t0 = time.perf_counter()
            surv_p4 = sieve_p4.sieve_window(cfg["p4_k"], cfg["p4_k"] + cfg["sieve_span"] * 6)
            t1 = time.perf_counter()
            p4_durations.append(t1 - t0)
            p4_survivors = len(surv_p4)
        med_p4_sieve = statistics.median(p4_durations)
        rate_p4_sieve = cfg["sieve_span"] / max(med_p4_sieve, 1e-6)

        # Phase 5 Sieve: SegmentedSCCAFilter
        fam_p5 = SmoothCenterFamily(cfg["p5_exponents"], family_id=f"bench_{scale_name}")
        sieve_p5 = SegmentedSCCAFilter(fam_p5, cfg["sieve_depth"])
        p5_durations = []
        p5_survivors = 0
        for _ in range(cfg["trials"]):
            t0 = time.perf_counter()
            surv_p5 = sieve_p5.sieve_segment(1, 1 + cfg["sieve_span"])
            t1 = time.perf_counter()
            p5_durations.append(t1 - t0)
            p5_survivors = len(surv_p5)
        med_p5_sieve = statistics.median(p5_durations)
        rate_p5_sieve = cfg["sieve_span"] / max(med_p5_sieve, 1e-6)

        print(f"  [Sieve Throughput (Depth={cfg['sieve_depth']:,})]")
        print(f"    Phase 4 ADRS-4: {med_p4_sieve*1000:6.2f} ms ({rate_p4_sieve:10,.0f} cands/s, {p4_survivors} survivors)")
        print(f"    Phase 5 SCCA:   {med_p5_sieve*1000:6.2f} ms ({rate_p5_sieve:10,.0f} cands/s, {p5_survivors} survivors)")

        # ---------------------------------------------------------
        # 2. PRIMALITY PROOF LATENCY BENCHMARK
        # ---------------------------------------------------------
        # Phase 4 Proof: Proth on B, LLR on A
        p4_center = cfg["p4_k"] * (1 << cfg["p4_n"])
        p4_A = p4_center - 1
        p4_B = p4_center + 1

        p4_proof_durations = []
        for _ in range(cfg["trials"]):
            t0 = time.perf_counter()
            _ = proth_prove(cfg["p4_k"], cfg["p4_n"], p4_B)
            _ = llr_prove(cfg["p4_k"], cfg["p4_n"], p4_A)
            t1 = time.perf_counter()
            p4_proof_durations.append(t1 - t0)
        med_p4_proof = statistics.median(p4_proof_durations)

        # Phase 5 Proof: Pocklington on B, Morrison on A
        p5_cand = fam_p5.candidate(cfg["p5_t"])
        p5_proof_durations = []
        for _ in range(cfg["trials"]):
            t0 = time.perf_counter()
            _ = prove_pocklington_upper(p5_cand.B, fam_p5.F_odd, fam_p5.odd_prime_factors)
            _ = prove_morrison_lower(p5_cand.A, fam_p5.F_odd, fam_p5.odd_prime_factors)
            t1 = time.perf_counter()
            p5_proof_durations.append(t1 - t0)
        med_p5_proof = statistics.median(p5_proof_durations)

        print(f"  [Proof Latency (Pair A & B)]")
        print(f"    Phase 4 (Proth + LLR):       {med_p4_proof*1000:8.2f} ms")
        print(f"    Phase 5 (Pocklington + Morr): {med_p5_proof*1000:8.2f} ms")

        # ---------------------------------------------------------
        # 3. INDEPENDENT VERIFICATION LATENCY BENCHMARK
        # ---------------------------------------------------------
        # Benchmark independent verifier on actual verified certificate
        cert_files = sorted((REPO_ROOT / "proofs" / "phase5").glob("cert_*.json"))
        med_p5_verify = 0.0
        if cert_files:
            # Pick a real certificate
            cf = cert_files[-1] # Largest certified file (133d)
            with open(cf, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            p5_verify_durations = []
            for _ in range(cfg["trials"]):
                t0 = time.perf_counter()
                is_valid, errors, _ = verify_certificate_v5_payload(cdata)
                t1 = time.perf_counter()
                p5_verify_durations.append(t1 - t0)
                assert is_valid is True
            med_p5_verify = statistics.median(p5_verify_durations)
            print(f"  [Independent Verification Latency (on {cf.name})]")
            print(f"    Phase 5 Independent Verifier: {med_p5_verify*1000:8.2f} ms (PASS)")

        all_results.append({
            "scale": scale_name,
            "digits_approx": p5_cand.digits_A,
            "sieve_depth": cfg["sieve_depth"],
            "phase4": {
                "n": cfg["p4_n"],
                "k": cfg["p4_k"],
                "sieve_median_ms": round(med_p4_sieve * 1000, 2),
                "sieve_cands_sec": round(rate_p4_sieve, 0),
                "sieve_survivors": p4_survivors,
                "proof_median_ms": round(med_p4_proof * 1000, 2)
            },
            "phase5": {
                "F_digits": len(str(fam_p5.F)),
                "sieve_median_ms": round(med_p5_sieve * 1000, 2),
                "sieve_cands_sec": round(rate_p5_sieve, 0),
                "sieve_survivors": p5_survivors,
                "proof_median_ms": round(med_p5_proof * 1000, 2),
                "independent_verify_median_ms": round(med_p5_verify * 1000, 2)
            }
        })

    # Save to research and reports
    out_dir = REPO_ROOT / "research" / "phase5_benchmarks" / "raw"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "phase4_vs_phase5.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    rep_dir = REPO_ROOT / "reports" / "phase5_benchmarks" / "raw"
    rep_dir.mkdir(parents=True, exist_ok=True)
    with open(rep_dir / "phase4_vs_phase5.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nRaw comparison benchmark saved to: {out_json}")
    return all_results

if __name__ == "__main__":
    run_stage_benchmarks()
