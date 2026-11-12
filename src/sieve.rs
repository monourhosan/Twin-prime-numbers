//! Dual-residue bitset sieves for bounded and structured twin-prime search.

use crate::bitset::BitSet;
use crate::primality::{generate_primes, mod_inverse};

/// Configuration and results for bounded-range twin-prime search.
pub struct BoundedTwinSieve {
    pub min_val: u64,
    pub max_val: u64,
    pub sieve_depth: u64,
    pub use_dual_sieve: bool,
}

impl BoundedTwinSieve {
    pub fn new(min_val: u64, max_val: u64, sieve_depth: u64, use_dual_sieve: bool) -> Self {
        Self {
            min_val,
            max_val,
            sieve_depth,
            use_dual_sieve,
        }
    }

    /// Executes the segmented sieve over centers m = 6r.
    /// Returns a list of candidate pairs (p, p+2) that survived the sieve.
    pub fn run_sieve(&self) -> (Vec<(u64, u64)>, SieveStats) {
        let mut stats = SieveStats::default();
        let mut candidates = Vec::new();

        // Edge case: pair (3, 5)
        if self.min_val <= 3 && self.max_val >= 5 {
            candidates.push((3, 5));
        }

        // Centers m = 6r
        // We require 6r - 1 >= min_val and 6r + 1 <= max_val
        let r_start = if self.min_val <= 5 {
            1
        } else {
            (self.min_val + 1 + 5) / 6
        };
        let r_end = if self.max_val < 7 {
            0
        } else {
            (self.max_val - 1) / 6
        };

        if r_start > r_end {
            stats.survivors = candidates.len();
            return (candidates, stats);
        }

        let num_r = (r_end - r_start + 1) as usize;
        stats.total_candidates = num_r;

        let mut bitset = BitSet::new_all_set(num_r);
        let q_limit = (self.sieve_depth as usize).min((self.max_val as f64).sqrt() as usize);
        let primes = generate_primes(q_limit);

        for &q_usize in &primes {
            let q = q_usize as u64;
            if q < 5 {
                continue; // 2 and 3 are handled by 6r +/- 1 structure
            }

            // 6 * r = +/- 1 mod q => r = +/- 6^(-1) mod q
            let inv6 = match mod_inverse(6, q as i64) {
                Some(inv) => inv as u64,
                None => continue,
            };
            let u1 = inv6 % q;
            let u2 = (q - u1) % q;

            if self.use_dual_sieve {
                // Eliminate both residue classes in unified traversal
                for &u in &[u1, u2] {
                    let mut first_r = if (r_start % q) <= u {
                        r_start + (u - (r_start % q))
                    } else {
                        r_start + (q + u - (r_start % q))
                    };

                    while first_r <= r_end {
                        // Check if 6r - 1 == q or 6r + 1 == q
                        let p1 = 6 * first_r - 1;
                        let p2 = 6 * first_r + 1;
                        if p1 != q && p2 != q {
                            let idx = (first_r - r_start) as usize;
                            bitset.clear(idx);
                        }
                        first_r += q;
                    }
                }
            } else {
                // Baseline: single residue pass
                let mut first_r1 = if (r_start % q) <= u1 {
                    r_start + (u1 - (r_start % q))
                } else {
                    r_start + (q + u1 - (r_start % q))
                };
                while first_r1 <= r_end {
                    let p1 = 6 * first_r1 - 1;
                    let p2 = 6 * first_r1 + 1;
                    if p1 != q && p2 != q {
                        bitset.clear((first_r1 - r_start) as usize);
                    }
                    first_r1 += q;
                }
                let mut first_r2 = if (r_start % q) <= u2 {
                    r_start + (u2 - (r_start % q))
                } else {
                    r_start + (q + u2 - (r_start % q))
                };
                while first_r2 <= r_end {
                    let p1 = 6 * first_r2 - 1;
                    let p2 = 6 * first_r2 + 1;
                    if p1 != q && p2 != q {
                        bitset.clear((first_r2 - r_start) as usize);
                    }
                    first_r2 += q;
                }
            }
        }

        for idx in bitset.iter_ones() {
            let r = r_start + idx as u64;
            candidates.push((6 * r - 1, 6 * r + 1));
        }

        stats.survivors = candidates.len();
        (candidates, stats)
    }
}

/// Sieve for structured twin candidates k * 2^n +/- 1.
pub struct StructuredTwinSieve {
    pub n: u32,
    pub k_min: u64,
    pub k_max: u64,
    pub sieve_depth: u64,
    pub use_dual_sieve: bool,
}

impl StructuredTwinSieve {
    pub fn new(n: u32, k_min: u64, k_max: u64, sieve_depth: u64, use_dual_sieve: bool) -> Self {
        // Enforce odd k
        let k_min_odd = if k_min % 2 == 0 { k_min + 1 } else { k_min };
        let k_max_odd = if k_max % 2 == 0 { k_max - 1 } else { k_max };
        Self {
            n,
            k_min: k_min_odd,
            k_max: k_max_odd,
            sieve_depth,
            use_dual_sieve,
        }
    }

    /// Sieves odd k in [k_min, k_max] eliminating k where k*2^n - 1 or k*2^n + 1 is divisible by q.
    pub fn run_sieve(&self) -> (Vec<u64>, SieveStats) {
        let mut stats = SieveStats::default();
        if self.k_min > self.k_max {
            return (Vec::new(), stats);
        }

        let num_odd_k = ((self.k_max - self.k_min) / 2 + 1) as usize;
        stats.total_candidates = num_odd_k;
        let mut bitset = BitSet::new_all_set(num_odd_k);

        let primes = generate_primes(self.sieve_depth as usize);

        for &q_usize in &primes {
            let q = q_usize as u64;
            if q == 2 {
                continue; // 2^n is coprime to odd primes, candidates are odd
            }

            // Compute a = 2^n mod q
            let a = mod_pow_u64(2, self.n as u64, q);
            if a == 0 {
                continue;
            }

            // Modular inverse of a modulo q
            let inv_a = match mod_inverse(a as i64, q as i64) {
                Some(inv) => inv as u64,
                None => continue,
            };

            // Residues for k mod q:
            // k * 2^n - 1 = 0 mod q => k = inv_a mod q
            // k * 2^n + 1 = 0 mod q => k = -inv_a mod q = (q - inv_a) mod q
            let u1 = inv_a % q;
            let u2 = (q - u1) % q;

            // In our compressed bitset, index i represents k = k_min + 2*i
            // 2*i = (u - k_min) mod q => i = 2^(-1) * (u - k_min) mod q
            let inv2 = (q + 1) / 2; // 2^(-1) mod odd prime q

            let residues = if self.use_dual_sieve {
                vec![u1, u2]
            } else {
                vec![u1, u2]
            };

            for &u in &residues {
                let diff = (u + q - (self.k_min % q)) % q;
                let step_start = (diff * inv2) % q;

                let mut idx = step_start as usize;
                while idx < num_odd_k {
                    bitset.clear(idx);
                    idx += q as usize;
                }
            }
        }

        let mut survivors = Vec::with_capacity(bitset.count_ones());
        for idx in bitset.iter_ones() {
            let k = self.k_min + 2 * (idx as u64);
            survivors.push(k);
        }

        stats.survivors = survivors.len();
        (survivors, stats)
    }
}

fn mod_pow_u64(mut base: u64, mut exp: u64, modulus: u64) -> u64 {
    let mut result = 1u64;
    base %= modulus;
    while exp > 0 {
        if exp % 2 == 1 {
            result = ((result as u128 * base as u128) % modulus as u128) as u64;
        }
        base = ((base as u128 * base as u128) % modulus as u128) as u64;
        exp >>= 1;
    }
    result
}

#[derive(Clone, Debug, Default)]
pub struct SieveStats {
    pub total_candidates: usize,
    pub survivors: usize,
}
