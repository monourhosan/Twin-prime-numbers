//! Adaptive Sieve Depth (ASD) cost modeling and scheduling.

/// Computes the theoretically and empirically optimal sieve depth Q*
/// based on candidate size (exponent n and coefficient range K).
pub fn estimate_optimal_sieve_depth(n: u32, k_range_size: u64) -> u64 {
    // Digits approximation: D ~ n * 0.30103 + log10(k)
    let bit_length = n as f64;

    // Big-integer multiplication cost scales roughly as O(bits^1.6) for Karatsuba / O(bits log bits)
    // Sieve cost per candidate scales as O(sum_{q<=Q} 2/q) ~ 2 ln(ln Q)
    // Survival probability S(Q) ~ C2 / (ln Q)^2
    // Optimal cutoff scales with bit_length^1.3 to balance sieve cache vs PRP throughput
    let base_q = 5_000.0 * (bit_length / 100.0).max(1.0).powf(1.35);

    // Clamp between sensible engineering bounds
    let q_clamped = base_q.clamp(1_000.0, 5_000_000.0) as u64;

    // Scale slightly with larger K batch sizes to amortize prime generation
    if k_range_size > 100_000 {
        (q_clamped * 2).min(10_000_000)
    } else {
        q_clamped
    }
}
