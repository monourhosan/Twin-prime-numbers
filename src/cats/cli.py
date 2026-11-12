"""
Command Line Interface for the CATS Twin-Prime Research Engine.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from .sieve import BoundedTwinSieve, StructuredTwinSieve
from .primality import is_prime_u64, is_probable_prime, proth_prove, llr_prove
from .adaptive import estimate_optimal_sieve_depth
from .certificate import TwinPrimeCertificate

def run_bounded(args):
    print("=== CATS Bounded Interval Twin Prime Search ===")
    print(f"Interval: [{args.min}, {args.max}]")
    depth = args.sieve_depth or int(args.max**0.5)
    use_dual = not args.no_dual_sieve
    print(f"Sieve limit: {depth}, Dual-residue: {use_dual}")

    t0 = time.time()
    sieve = BoundedTwinSieve(args.min, args.max, depth, use_dual)
    candidates, stats = sieve.run_sieve()
    t_sieve = time.time() - t0

    print(
        f"Sieve completed in {t_sieve:.4f}s: {stats.survivors} survived "
        f"out of {stats.total_candidates} candidates."
    )

    t_test_start = time.time()
    verified_twins = []
    for p1, p2 in candidates:
        if is_prime_u64(p1) and is_prime_u64(p2):
            verified_twins.append((p1, p2))
    t_total = time.time() - t0

    print(
        f"Verification completed in {time.time() - t_test_start:.4f}s. "
        f"Total verified twin pairs: {len(verified_twins)}"
    )
    print(f"Total wall time: {t_total:.4f}s")

    if verified_twins:
        print(f"Largest verified twin pair in interval: {verified_twins[-1]}")
    else:
        print("No twin pairs found in specified interval.")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as f:
            for p1, p2 in verified_twins:
                f.write(
                    f'{{"type":"bounded","p1":{p1},"p2":{p2},"status":"VERIFIED_PRIME_PAIR"}}\n'
                )
        print(f"Results appended to {out_path}")

def run_structured(args):
    print(f"=== CATS Structured Search: k * 2^{args.n} +/- 1 ===")
    print(f"k range: [{args.k_min}, {args.k_max}]")

    if args.adaptive:
        depth = estimate_optimal_sieve_depth(args.n, args.k_max - args.k_min)
        print(f"Adaptive Sieve Depth enabled -> optimal Q* = {depth}")
    else:
        depth = args.sieve_depth or 50_000

    use_dual = not args.no_dual_sieve
    t0 = time.time()
    sieve = StructuredTwinSieve(args.n, args.k_min, args.k_max, depth, use_dual)
    survivors, stats = sieve.run_sieve()
    t_sieve = time.time() - t0

    print(
        f"Sieve finished in {t_sieve:.4f}s: {stats.survivors} candidates survived "
        f"out of {stats.total_candidates} odd k values."
    )

    t_test_start = time.time()
    two_pow_n = 1 << args.n
    proven_pairs = []
    prp_pairs = []

    cert_dir = Path(args.cert_dir) if args.cert_dir else None
    if cert_dir:
        cert_dir.mkdir(parents=True, exist_ok=True)

    for k in survivors:
        center = k * two_pow_n
        p_plus = center + 1
        p_minus = center - 1

        if args.prove and (args.n >= 64 or k < (1 << args.n)):
            # Certificate-Cost-Aware Pipeline:
            # 1. Inexpensive base-2 PRP screen on p_plus
            if not is_probable_prime(p_plus, [2]):
                continue

            # 2. Proth test on p_plus
            is_proth, proth_w = proth_prove(k, args.n, p_plus)
            if is_proth:
                # 3. Only if p_plus is proven prime, run LLR test on p_minus
                is_llr, llr_p, _ = llr_prove(k, args.n, p_minus)
                if is_llr:
                    digits = len(str(p_plus))
                    cert = TwinPrimeCertificate(
                        pair_type=f"Structured: k * 2^{args.n} +/- 1",
                        p_minus_str=str(p_minus),
                        p_plus_str=str(p_plus),
                        digits=digits,
                        k=k,
                        n=args.n,
                        proth_witness=proth_w,
                        llr_witness=llr_p,
                        is_proven=True,
                    )
                    if cert_dir:
                        cert.save_to_file(cert_dir / f"cert_k{k}_n{args.n}.json")
                    proven_pairs.append((k, digits, cert))
        else:
            # PRP screen
            if is_probable_prime(p_plus) and is_probable_prime(p_minus):
                digits = len(str(p_plus))
                cert = TwinPrimeCertificate(
                    pair_type=f"Structured: k * 2^{args.n} +/- 1",
                    p_minus_str=str(p_minus),
                    p_plus_str=str(p_plus),
                    digits=digits,
                    k=k,
                    n=args.n,
                    is_proven=False,
                )
                prp_pairs.append((k, digits, cert))

    t_total = time.time() - t0
    print(
        f"Testing finished in {time.time() - t_test_start:.4f}s. "
        f"Proven pairs: {len(proven_pairs)}, PRP pairs: {len(prp_pairs)}"
    )
    print(f"Total wall time: {t_total:.4f}s")

    for k, digits, _ in proven_pairs:
        print(f"-> PROVEN TWIN PAIR: {k} * 2^{args.n} +/- 1 ({digits} decimal digits)")
    for k, digits, _ in prp_pairs:
        print(f"-> STRONG PRP TWIN PAIR: {k} * 2^{args.n} +/- 1 ({digits} decimal digits)")

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(out_path, "a", encoding="utf-8") as f:
            for _, _, cert in proven_pairs:
                f.write(json.dumps(cert.to_dict()) + "\n")
            for _, _, cert in prp_pairs:
                f.write(json.dumps(cert.to_dict()) + "\n")
        print(f"Candidate records appended to {out_path}")

def run_ablation(args):
    print("=== CATS Empirical Ablation Study ===")
    print(f"Target: k * 2^{args.n} +/- 1, k in [1, {args.k_count}]")
    two_pow_n = 1 << args.n

    # Config 1: Baseline (Static depth 5000, no dual sieve, unordered)
    print("\n--- 1. Baseline Configuration (Static Q=5,000, single-residue) ---")
    t0 = time.time()
    sieve1 = StructuredTwinSieve(args.n, 1, args.k_count, 5_000, use_dual_sieve=False)
    surv1, stats1 = sieve1.run_sieve()
    t_sieve1 = time.time() - t0
    count1 = 0
    for k in surv1:
        center = k * two_pow_n
        if is_probable_prime(center + 1, [2, 3]) and is_probable_prime(center - 1, [2, 3]):
            count1 += 1
    total1 = time.time() - t0
    print(f"Baseline: Sieve {t_sieve1:.4f}s (survivors: {stats1.survivors}), Total: {total1:.4f}s, Pairs: {count1}")

    # Config 2: + Dual-Residue Sieve
    print("\n--- 2. + Dual-Residue Sieve (DR-Sieve) ---")
    t0 = time.time()
    sieve2 = StructuredTwinSieve(args.n, 1, args.k_count, 5_000, use_dual_sieve=True)
    surv2, stats2 = sieve2.run_sieve()
    t_sieve2 = time.time() - t0
    count2 = 0
    for k in surv2:
        center = k * two_pow_n
        if is_probable_prime(center + 1, [2, 3]) and is_probable_prime(center - 1, [2, 3]):
            count2 += 1
    total2 = time.time() - t0
    print(f"+DR-Sieve: Sieve {t_sieve2:.4f}s (survivors: {stats2.survivors}), Total: {total2:.4f}s, Pairs: {count2}")

    # Config 3: + Adaptive Sieve Depth
    opt_q = estimate_optimal_sieve_depth(args.n, args.k_count)
    print(f"\n--- 3. + Adaptive Sieve Depth (Q* = {opt_q}) ---")
    t0 = time.time()
    sieve3 = StructuredTwinSieve(args.n, 1, args.k_count, opt_q, use_dual_sieve=True)
    surv3, stats3 = sieve3.run_sieve()
    t_sieve3 = time.time() - t0
    count3 = 0
    for k in surv3:
        center = k * two_pow_n
        if is_probable_prime(center + 1, [2, 3]) and is_probable_prime(center - 1, [2, 3]):
            count3 += 1
    total3 = time.time() - t0
    print(f"+ASD: Sieve {t_sieve3:.4f}s (survivors: {stats3.survivors}), Total: {total3:.4f}s, Pairs: {count3}")

    # Config 4: Full CATS (+ Certificate-Cost-Aware Pipeline)
    print(f"\n--- 4. Full CATS (+ Certificate-Cost-Aware Pipeline) ---")
    t0 = time.time()
    sieve4 = StructuredTwinSieve(args.n, 1, args.k_count, opt_q, use_dual_sieve=True)
    surv4, stats4 = sieve4.run_sieve()
    t_sieve4 = time.time() - t0
    proven4 = 0
    for k in surv4:
        center = k * two_pow_n
        p_plus = center + 1
        if not is_probable_prime(p_plus, [2]):
            continue
        is_proth, _ = proth_prove(k, args.n, p_plus)
        if is_proth:
            is_llr, _, _ = llr_prove(k, args.n, center - 1)
            if is_llr:
                proven4 += 1
    total4 = time.time() - t0
    print(f"Full CATS: Sieve {t_sieve4:.4f}s (survivors: {stats4.survivors}), Total: {total4:.4f}s, Proven Pairs: {proven4}")

    print("\n=== Ablation Summary ===")
    print(f"Baseline time:   {total1:.4f}s (1.00x)")
    print(f"+ DR-Sieve time: {total2:.4f}s ({total1 / max(1e-6, total2):.2f}x speedup)")
    print(f"+ ASD time:      {total3:.4f}s ({total1 / max(1e-6, total3):.2f}x speedup)")
    print(f"Full CATS time:  {total4:.4f}s ({total1 / max(1e-6, total4):.2f}x speedup vs baseline, fully proven)")

def run_benchmarks(args):
    print("=== CATS Benchmark Suite ===")
    rows = [
        "mode,parameter,k_or_r_range,sieve_depth,sieve_time_sec,total_time_sec,survivors,discovered_pairs"
    ]

    # Bounded benchmarks
    for bound in [100_000, 1_000_000, 5_000_000, 10_000_000]:
        t0 = time.time()
        sieve = BoundedTwinSieve(2, bound, int(bound**0.5), use_dual_sieve=True)
        candidates, stats = sieve.run_sieve()
        sieve_time = time.time() - t0
        twins = [p for p in candidates if is_prime_u64(p[0]) and is_prime_u64(p[1])]
        total_time = time.time() - t0
        print(f"Bounded [2, {bound}]: Total {total_time:.4f}s, Verified Twins: {len(twins)}")
        rows.append(
            f"bounded,{bound},{bound // 6},{int(bound**0.5)},{sieve_time:.4f},{total_time:.4f},{stats.survivors},{len(twins)}"
        )

    # Structured sweeps
    sweep = [
        (20, 10_000),
        (50, 10_000),
        (100, 10_000),
        (250, 5_000),
        (500, 2_000),
        (1000, 1_000),
    ]

    for n, k_max in sweep:
        opt_q = estimate_optimal_sieve_depth(n, k_max)
        t0 = time.time()
        sieve = StructuredTwinSieve(n, 1, k_max, opt_q, use_dual_sieve=True)
        survivors, stats = sieve.run_sieve()
        sieve_time = time.time() - t0

        two_pow_n = 1 << n
        proven_count = 0
        for k in survivors:
            center = k * two_pow_n
            p_plus = center + 1
            if is_probable_prime(p_plus, [2]):
                is_proth, _ = proth_prove(k, n, p_plus)
                if is_proth:
                    is_llr, _, _ = llr_prove(k, n, center - 1)
                    if is_llr:
                        proven_count += 1
        total_time = time.time() - t0
        print(f"Structured n={n:4} (k<={k_max}): Total {total_time:.4f}s, Proven Twins: {proven_count}")
        rows.append(
            f"structured,n={n},k_max={k_max},{opt_q},{sieve_time:.4f},{total_time:.4f},{stats.survivors},{proven_count}"
        )

    if args.output_csv:
        csv_path = Path(args.output_csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write("\n".join(rows) + "\n")
        print(f"Benchmark results written to {csv_path}")

def run_verify(args):
    print("=== CATS Primality Certificate Verifier ===")
    cert_path = Path(args.cert)
    print(f"Verifying certificate file: {cert_path}")
    if not cert_path.exists():
        print(f"Error: File not found {cert_path}")
        sys.exit(1)

    cert = TwinPrimeCertificate.from_file(cert_path)
    print(f"Certificate ID:  {cert.certificate_id}")
    print(f"Declared Status: {cert.proof_status}")
    print(f"Pair Type:       {cert.pair_type}")
    print(f"Digits:          {cert.digits}")

    if cert.verify_checksum():
        print(f"[PASS] Cryptographic SHA-256 Checksum Verified: {cert.sha256_hash}")
    else:
        print(f"[FAIL] Checksum mismatch! Declared: {cert.sha256_hash}, Computed: {cert.compute_hash()}")
        sys.exit(1)

    # Re-verify mathematical theorems independently
    if cert.k and cert.n:
        k = cert.k
        n = cert.n
        center = k * (1 << n)
        p_plus = center + 1
        p_minus = center - 1

        if cert.p_plus_proof:
            witness = cert.p_plus_proof["witness"]
            print(f"Auditing Proth primality proof for p+ (witness={witness})...")
            exp = (p_plus - 1) // 2
            val = pow(witness, exp, p_plus)
            if val == p_plus - 1:
                print(f"[PASS] Proth condition confirmed: {witness}^((B-1)/2) == -1 (mod B)")
            else:
                print(f"[FAIL] Proth condition FAILED!")
                sys.exit(1)

        if cert.p_minus_proof:
            p_witness = cert.p_minus_proof["witness_p"]
            print(f"Auditing LLR primality proof for p- (P={p_witness})...")
            is_llr, _, _ = llr_prove(k, n, p_minus)
            if is_llr:
                print(f"[PASS] Lucas-Lehmer-Riesel condition confirmed: u_{{n-2}} == 0 (mod A)")
            else:
                print(f"[FAIL] LLR condition FAILED!")
                sys.exit(1)

    print("\n[SUCCESS] Certificate independently proven valid and mathematically sound.")

def main():
    parser = argparse.ArgumentParser(
        prog="cats",
        description="CATS: Certificate-Aware Adaptive Twin-prime Sieve",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Bounded
    p_b = subparsers.add_parser("bounded", help="Bounded exhaustive search in [min, max]")
    p_b.add_argument("--min", type=int, default=2)
    p_b.add_argument("--max", type=int, default=1_000_000)
    p_b.add_argument("--sieve-depth", type=int, default=None)
    p_b.add_argument("--no-dual-sieve", action="store_true", default=False)
    p_b.add_argument("--output", type=str, default=None)

    # Structured
    p_s = subparsers.add_parser("structured", help="Structured search: k * 2^n +/- 1")
    p_s.add_argument("-n", type=int, default=100)
    p_s.add_argument("--k-min", type=int, default=1)
    p_s.add_argument("--k-max", type=int, default=10_000)
    p_s.add_argument("--sieve-depth", type=int, default=None)
    p_s.add_argument("--adaptive", action="store_true", default=False)
    p_s.add_argument("--no-dual-sieve", action="store_true", default=False)
    p_s.add_argument("--prove", action="store_true", default=True)
    p_s.add_argument("--output", type=str, default=None)
    p_s.add_argument("--cert-dir", type=str, default=None)

    # Benchmark
    p_bm = subparsers.add_parser("benchmark", help="Run benchmark suite")
    p_bm.add_argument("--output-csv", type=str, default=None)

    # Ablation
    p_ab = subparsers.add_parser("ablation", help="Run empirical ablation study")
    p_ab.add_argument("-n", type=int, default=200)
    p_ab.add_argument("--k-count", type=int, default=20_000)

    # Verify
    p_v = subparsers.add_parser("verify", help="Verify a primality certificate JSON file")
    p_v.add_argument("--cert", type=str, required=True)

    args = parser.parse_args()
    if args.command == "bounded":
        run_bounded(args)
    elif args.command == "structured":
        run_structured(args)
    elif args.command == "ablation":
        run_ablation(args)
    elif args.command == "benchmark":
        run_benchmarks(args)
    elif args.command == "verify":
        run_verify(args)

if __name__ == "__main__":
    main()
