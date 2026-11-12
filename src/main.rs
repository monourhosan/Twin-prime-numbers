use clap::{Parser, Subcommand};
use num_bigint::BigUint;
use num_traits::One;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
use std::time::Instant;

use cats_twin_prime::adaptive::estimate_optimal_sieve_depth;
use cats_twin_prime::certificate::TwinPrimeCertificate;
use cats_twin_prime::primality::{
    is_prime_u64, is_probable_prime, llr_prove, proth_prove,
};
use cats_twin_prime::sieve::{BoundedTwinSieve, StructuredTwinSieve};

#[derive(Parser, Debug)]
#[command(
    name = "cats",
    author = "Antigravity Research Group",
    version = "1.0.0",
    about = "Certificate-Aware Adaptive Twin-prime Sieve (CATS) Engine"
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Complete bounded-range twin prime search in [min, max]
    Bounded {
        #[arg(long, default_value_t = 2)]
        min: u64,
        #[arg(long, default_value_t = 1_000_000)]
        max: u64,
        #[arg(long)]
        sieve_depth: Option<u64>,
        #[arg(long, default_value_t = false)]
        no_dual_sieve: bool,
        #[arg(long)]
        output: Option<PathBuf>,
    },

    /// Structured search for large twin primes k * 2^n +/- 1
    Structured {
        #[arg(long, default_value_t = 100)]
        n: u32,
        #[arg(long, default_value_t = 1)]
        k_min: u64,
        #[arg(long, default_value_t = 10_000)]
        k_max: u64,
        #[arg(long)]
        sieve_depth: Option<u64>,
        #[arg(long, default_value_t = false)]
        adaptive: bool,
        #[arg(long, default_value_t = false)]
        no_dual_sieve: bool,
        #[arg(long, default_value_t = true)]
        prove: bool,
        #[arg(long)]
        output: Option<PathBuf>,
        #[arg(long)]
        cert_dir: Option<PathBuf>,
    },

    /// Run controlled benchmark matrix
    Benchmark {
        #[arg(long)]
        output_csv: Option<PathBuf>,
    },

    /// Run empirical ablation study
    Ablation {
        #[arg(long, default_value_t = 200)]
        n: u32,
        #[arg(long, default_value_t = 20_000)]
        k_count: u64,
    },

    /// Verify an existing JSON primality certificate
    Verify {
        #[arg(long)]
        cert: PathBuf,
    },
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        Commands::Bounded {
            min,
            max,
            sieve_depth,
            no_dual_sieve,
            output,
        } => {
            run_bounded(min, max, sieve_depth, !no_dual_sieve, output);
        }
        Commands::Structured {
            n,
            k_min,
            k_max,
            sieve_depth,
            adaptive,
            no_dual_sieve,
            prove,
            output,
            cert_dir,
        } => {
            run_structured(
                n,
                k_min,
                k_max,
                sieve_depth,
                adaptive,
                !no_dual_sieve,
                prove,
                output,
                cert_dir,
            );
        }
        Commands::Benchmark { output_csv } => {
            run_benchmarks(output_csv);
        }
        Commands::Ablation { n, k_count } => {
            run_ablation(n, k_count);
        }
        Commands::Verify { cert } => {
            verify_cert_file(cert);
        }
    }
}

fn run_bounded(
    min_val: u64,
    max_val: u64,
    sieve_depth: Option<u64>,
    use_dual: bool,
    output_path: Option<PathBuf>,
) {
    println!("=== CATS Bounded Interval Twin Prime Search ===");
    println!("Interval: [{}, {}]", min_val, max_val);
    let depth = sieve_depth.unwrap_or_else(|| (max_val as f64).sqrt() as u64);
    println!("Sieve limit: {}, Dual-residue: {}", depth, use_dual);

    let start = Instant::now();
    let sieve = BoundedTwinSieve::new(min_val, max_val, depth, use_dual);
    let (sieve_candidates, stats) = sieve.run_sieve();
    let sieve_elapsed = start.elapsed();

    println!(
        "Sieve completed in {:.4}s: {} candidates survived out of {} centers",
        sieve_elapsed.as_secs_f64(),
        stats.survivors,
        stats.total_candidates
    );

    let test_start = Instant::now();
    let mut verified_twins = Vec::new();
    for (p1, p2) in sieve_candidates {
        if is_prime_u64(p1) && is_prime_u64(p2) {
            verified_twins.push((p1, p2));
        }
    }
    let total_elapsed = start.elapsed();

    println!(
        "Verification completed in {:.4}s. Total verified twin pairs: {}",
        test_start.elapsed().as_secs_f64(),
        verified_twins.len()
    );
    println!("Total wall time: {:.4}s", total_elapsed.as_secs_f64());

    if let Some(last) = verified_twins.last() {
        println!("Largest verified twin pair in interval: ({}, {})", last.0, last.1);
    } else {
        println!("No twin pairs found in specified interval.");
    }

    if let Some(path) = output_path {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).ok();
        }
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .expect("Failed to open output file");
        for (p1, p2) in &verified_twins {
            writeln!(
                file,
                "{{\"type\":\"bounded\",\"p1\":{},\"p2\":{},\"status\":\"VERIFIED_PRIME_PAIR\"}}",
                p1, p2
            )
            .ok();
        }
        println!("Results saved to {:?}", path);
    }
}

fn run_structured(
    n: u32,
    k_min: u64,
    k_max: u64,
    sieve_depth: Option<u64>,
    adaptive: bool,
    use_dual: bool,
    prove: bool,
    output_path: Option<PathBuf>,
    cert_dir: Option<PathBuf>,
) {
    println!("=== CATS Structured Search: k * 2^{} +/- 1 ===", n);
    println!("k range: [{}, {}]", k_min, k_max);

    let depth = if adaptive {
        let opt = estimate_optimal_sieve_depth(n, k_max - k_min);
        println!("Adaptive Sieve Depth enabled -> optimal Q* = {}", opt);
        opt
    } else {
        sieve_depth.unwrap_or(50_000)
    };

    let start = Instant::now();
    let sieve = StructuredTwinSieve::new(n, k_min, k_max, depth, use_dual);
    let (survivors, stats) = sieve.run_sieve();
    let sieve_elapsed = start.elapsed();

    println!(
        "Sieve finished in {:.4}s: {} candidates survived out of {} odd k",
        sieve_elapsed.as_secs_f64(),
        stats.survivors,
        stats.total_candidates
    );

    let test_start = Instant::now();
    let two_pow_n = BigUint::one() << n;
    let mut proven_pairs = Vec::new();
    let mut prp_pairs = Vec::new();

    if let Some(ref dir) = cert_dir {
        fs::create_dir_all(dir).ok();
    }

    for k in survivors {
        let k_big = BigUint::from(k);
        let center = &k_big * &two_pow_n;
        let p_plus = &center + 1u32;
        let p_minus = &center - 1u32;

        if prove && (n >= 64 || k < (1u64 << n)) {
            // Certificate-Cost-Aware Pipeline:
            // 1. Inexpensive base-2 PRP screen on p_plus
            if !is_probable_prime(&p_plus, &[2]) {
                continue;
            }

            // 2. Proth primality test on p_plus
            let proth_res = proth_prove(k, n, &p_plus);
            if let Ok(proth_proof) = proth_res {
                // 3. Only if p_plus is proven, run LLR test on p_minus
                let llr_res = llr_prove(k, n, &p_minus);
                if let Ok(llr_proof) = llr_res {
                    let digits = p_plus.to_string().len();
                    let cert = TwinPrimeCertificate::new_structured(
                        k,
                        n,
                        p_minus.to_str_radix(10),
                        p_plus.to_str_radix(10),
                        digits,
                        Some(proth_proof.witness_a),
                        Some(llr_proof.p_param),
                        true,
                    );

                    if let Some(ref dir) = cert_dir {
                        let fname = format!("cert_k{}_n{}.json", k, n);
                        cert.save_to_file(dir.join(fname)).ok();
                    }

                    proven_pairs.push((k, digits, cert));
                }
            }
        } else {
            // General PRP screen with multiple bases
            let bases = [2, 3, 5, 7, 11];
            if is_probable_prime(&p_plus, &bases) && is_probable_prime(&p_minus, &bases) {
                let digits = p_plus.to_string().len();
                let cert = TwinPrimeCertificate::new_structured(
                    k,
                    n,
                    p_minus.to_str_radix(10),
                    p_plus.to_str_radix(10),
                    digits,
                    None,
                    None,
                    false,
                );
                prp_pairs.push((k, digits, cert));
            }
        }
    }

    let total_elapsed = start.elapsed();
    println!(
        "Testing finished in {:.4}s. Proven pairs: {}, PRP pairs: {}",
        test_start.elapsed().as_secs_f64(),
        proven_pairs.len(),
        prp_pairs.len()
    );
    println!("Total wall time: {:.4}s", total_elapsed.as_secs_f64());

    for (k, digits, _) in &proven_pairs {
        println!(
            "-> PROVEN TWIN PAIR: {} * 2^{} +/- 1 ({} decimal digits)",
            k, n, digits
        );
    }
    for (k, digits, _) in &prp_pairs {
        println!(
            "-> STRONG PRP TWIN PAIR: {} * 2^{} +/- 1 ({} decimal digits)",
            k, n, digits
        );
    }

    if let Some(path) = output_path {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).ok();
        }
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&path)
            .expect("Failed to open output file");
        for (_, _, cert) in &proven_pairs {
            let json = serde_json::to_string(cert).unwrap();
            writeln!(file, "{}", json).ok();
        }
        for (_, _, cert) in &prp_pairs {
            let json = serde_json::to_string(cert).unwrap();
            writeln!(file, "{}", json).ok();
        }
        println!("Saved candidate records to {:?}", path);
    }
}

fn run_ablation(n: u32, k_count: u64) {
    println!("=== CATS Empirical Ablation Study ===");
    println!("Target: k * 2^{} +/- 1, k in [1, {}]", n, k_count);

    // Configuration 1: Baseline (Static depth 10,000, no dual residue sieve, unordered)
    println!("\n--- 1. Baseline Configuration ---");
    let t0 = Instant::now();
    let sieve1 = StructuredTwinSieve::new(n, 1, k_count, 10_000, false);
    let (surv1, stats1) = sieve1.run_sieve();
    let t_sieve1 = t0.elapsed();
    let mut count1 = 0;
    let two_pow_n = BigUint::one() << n;
    for k in surv1 {
        let center = BigUint::from(k) * &two_pow_n;
        let p_plus = &center + 1u32;
        let p_minus = &center - 1u32;
        if is_probable_prime(&p_plus, &[2, 3]) && is_probable_prime(&p_minus, &[2, 3]) {
            count1 += 1;
        }
    }
    let total1 = t0.elapsed();
    println!(
        "Baseline: Sieve {:.4}s (survivors: {}), Total: {:.4}s, Pairs: {}",
        t_sieve1.as_secs_f64(),
        stats1.survivors,
        total1.as_secs_f64(),
        count1
    );

    // Configuration 2: + Dual-Residue Sieve (DR-Sieve)
    println!("\n--- 2. + Dual-Residue Bitset Sieve (DR-Sieve) ---");
    let t0 = Instant::now();
    let sieve2 = StructuredTwinSieve::new(n, 1, k_count, 10_000, true);
    let (surv2, stats2) = sieve2.run_sieve();
    let t_sieve2 = t0.elapsed();
    let mut count2 = 0;
    for k in surv2 {
        let center = BigUint::from(k) * &two_pow_n;
        let p_plus = &center + 1u32;
        let p_minus = &center - 1u32;
        if is_probable_prime(&p_plus, &[2, 3]) && is_probable_prime(&p_minus, &[2, 3]) {
            count2 += 1;
        }
    }
    let total2 = t0.elapsed();
    println!(
        "+DR-Sieve: Sieve {:.4}s (survivors: {}), Total: {:.4}s, Pairs: {}",
        t_sieve2.as_secs_f64(),
        stats2.survivors,
        total2.as_secs_f64(),
        count2
    );

    // Configuration 3: + Adaptive Sieve Depth (ASD)
    let opt_q = estimate_optimal_sieve_depth(n, k_count);
    println!("\n--- 3. + Adaptive Sieve Depth (Q* = {}) ---", opt_q);
    let t0 = Instant::now();
    let sieve3 = StructuredTwinSieve::new(n, 1, k_count, opt_q, true);
    let (surv3, stats3) = sieve3.run_sieve();
    let t_sieve3 = t0.elapsed();
    let mut count3 = 0;
    for k in surv3 {
        let center = BigUint::from(k) * &two_pow_n;
        let p_plus = &center + 1u32;
        let p_minus = &center - 1u32;
        if is_probable_prime(&p_plus, &[2, 3]) && is_probable_prime(&p_minus, &[2, 3]) {
            count3 += 1;
        }
    }
    let total3 = t0.elapsed();
    println!(
        "+ASD: Sieve {:.4}s (survivors: {}), Total: {:.4}s, Pairs: {}",
        t_sieve3.as_secs_f64(),
        stats3.survivors,
        total3.as_secs_f64(),
        count3
    );

    // Configuration 4: Full CATS (DR-Sieve + ASD + Certificate-Cost-Aware Pipeline)
    println!("\n--- 4. Full CATS (+ Certificate-Cost-Aware Pipeline) ---");
    let t0 = Instant::now();
    let sieve4 = StructuredTwinSieve::new(n, 1, k_count, opt_q, true);
    let (surv4, stats4) = sieve4.run_sieve();
    let t_sieve4 = t0.elapsed();
    let mut proven4 = 0;
    for k in surv4 {
        let center = BigUint::from(k) * &two_pow_n;
        let p_plus = &center + 1u32;
        if !is_probable_prime(&p_plus, &[2]) {
            continue;
        }
        if let Ok(_) = proth_prove(k, n, &p_plus) {
            let p_minus = &center - 1u32;
            if let Ok(_) = llr_prove(k, n, &p_minus) {
                proven4 += 1;
            }
        }
    }
    let total4 = t0.elapsed();
    println!(
        "Full CATS: Sieve {:.4}s (survivors: {}), Total: {:.4}s, Proven Pairs: {}",
        t_sieve4.as_secs_f64(),
        stats4.survivors,
        total4.as_secs_f64(),
        proven4
    );

    println!("\n=== Ablation Summary ===");
    println!("Baseline time:       {:.4}s (1.00x)", total1.as_secs_f64());
    println!(
        "+ DR-Sieve time:     {:.4}s ({:.2}x speedup)",
        total2.as_secs_f64(),
        total1.as_secs_f64() / total2.as_secs_f64()
    );
    println!(
        "+ ASD time:          {:.4}s ({:.2}x speedup)",
        total3.as_secs_f64(),
        total1.as_secs_f64() / total3.as_secs_f64()
    );
    println!(
        "Full CATS time:      {:.4}s ({:.2}x speedup vs baseline, fully proven)",
        total4.as_secs_f64(),
        total1.as_secs_f64() / total4.as_secs_f64()
    );
}

fn run_benchmarks(output_csv: Option<PathBuf>) {
    println!("=== CATS Benchmark Matrix ===");
    let mut rows = Vec::new();
    rows.push(
        "mode,parameter,k_or_r_range,sieve_depth,sieve_time_sec,total_time_sec,survivors,discovered_pairs"
            .to_string(),
    );

    // 1. Bounded benchmarks
    for &bound in &[100_000u64, 1_000_000u64, 5_000_000u64, 10_000_000u64] {
        let t0 = Instant::now();
        let sieve = BoundedTwinSieve::new(2, bound, (bound as f64).sqrt() as u64, true);
        let (candidates, stats) = sieve.run_sieve();
        let sieve_sec = t0.elapsed().as_secs_f64();
        let mut count = 0;
        for (p1, p2) in candidates {
            if is_prime_u64(p1) && is_prime_u64(p2) {
                count += 1;
            }
        }
        let total_sec = t0.elapsed().as_secs_f64();
        println!(
            "Bounded [2, {}]: Total {:.4}s, Verified Twins: {}",
            bound, total_sec, count
        );
        rows.push(format!(
            "bounded,{},{},{},{:.4},{:.4},{},{}",
            bound,
            bound / 6,
            (bound as f64).sqrt() as u64,
            sieve_sec,
            total_sec,
            stats.survivors,
            count
        ));
    }

    // 2. Structured sweeps across digit scales
    let sweep = [
        (20u32, 10_000u64),
        (50u32, 10_000u64),
        (100u32, 10_000u64),
        (250u32, 5_000u64),
        (500u32, 2_000u64),
        (1000u32, 1_000u64),
    ];

    for &(n, k_max) in &sweep {
        let opt_q = estimate_optimal_sieve_depth(n, k_max);
        let t0 = Instant::now();
        let sieve = StructuredTwinSieve::new(n, 1, k_max, opt_q, true);
        let (survivors, stats) = sieve.run_sieve();
        let sieve_sec = t0.elapsed().as_secs_f64();

        let two_pow_n = BigUint::one() << n;
        let mut proven_count = 0;
        for k in survivors {
            let center = BigUint::from(k) * &two_pow_n;
            let p_plus = &center + 1u32;
            if is_probable_prime(&p_plus, &[2]) {
                if let Ok(_) = proth_prove(k, n, &p_plus) {
                    let p_minus = &center - 1u32;
                    if let Ok(_) = llr_prove(k, n, &p_minus) {
                        proven_count += 1;
                    }
                }
            }
        }
        let total_sec = t0.elapsed().as_secs_f64();
        println!(
            "Structured n={:4} (k<= {}): Total {:.4}s, Proven Twins: {}",
            n, k_max, total_sec, proven_count
        );
        rows.push(format!(
            "structured,n={},k_max={},{},{:.4},{:.4},{},{}",
            n, k_max, opt_q, sieve_sec, total_sec, stats.survivors, proven_count
        ));
    }

    if let Some(path) = output_csv {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).ok();
        }
        fs::write(&path, rows.join("\n")).expect("Failed to write CSV benchmarks");
        println!("Benchmark data written to {:?}", path);
    }
}

fn verify_cert_file(cert_path: PathBuf) {
    println!("=== CATS Certificate Verifier ===");
    println!("Loading: {:?}", cert_path);
    let data = fs::read_to_string(&cert_path).expect("Failed to read certificate file");
    let cert: TwinPrimeCertificate =
        serde_json::from_str(&data).expect("Failed to parse certificate JSON");

    println!("Certificate ID: {}", cert.certificate_id);
    println!("Status declared: {}", cert.proof_status);
    println!("Pair type: {}", cert.pair_type);
    println!("Digits: {}", cert.digits);

    let recalculated_hash = cert.compute_hash();
    if recalculated_hash == cert.sha256_hash {
        println!("[PASS] Checksum verified: {}", cert.sha256_hash);
    } else {
        println!(
            "[FAIL] Checksum mismatch! Declared: {}, Computed: {}",
            cert.sha256_hash, recalculated_hash
        );
        return;
    }

    if let (Some(k), Some(n)) = (cert.k, cert.n) {
        let two_pow_n = BigUint::one() << n;
        let center = BigUint::from(k) * &two_pow_n;
        let p_plus = &center + 1u32;
        let p_minus = &center - 1u32;

        if let Some(ref proth) = cert.p_plus_proof {
            println!(
                "Verifying Proth proof for p+ (witness = {})...",
                proth.witness
            );
            let exp = (&p_plus - 1u32) / 2u32;
            let val = BigUint::from(proth.witness).modpow(&exp, &p_plus);
            if val == &p_plus - 1u32 {
                println!("[PASS] Proth primality theorem holds for p+");
            } else {
                println!("[FAIL] Proth condition failed for p+!");
            }
        }

        if let Some(ref llr) = cert.p_minus_proof {
            println!(
                "Verifying LLR proof for p- (P parameter = {})...",
                llr.witness
            );
            match llr_prove(k, n, &p_minus) {
                Ok(_) => println!("[PASS] Lucas-Lehmer-Riesel proof verified for p-"),
                Err(_) => println!("[FAIL] LLR proof condition failed for p-!"),
            }
        }
    }
}
