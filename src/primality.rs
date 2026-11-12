//! Primality testing and deterministic certification module.
//!
//! Implements:
//! - Small prime sieving for factor bases
//! - Deterministic 64-bit Miller-Rabin test
//! - Multiprecision Miller-Rabin strong probable prime test
//! - Proth's theorem primality prover for k * 2^n + 1
//! - Lucas-Lehmer-Riesel (LLR) / BLS Theorem 8 primality prover for k * 2^n - 1

use num_bigint::{BigInt, BigUint, ToBigInt};
use num_integer::Integer;
use num_traits::{One, Zero, ToPrimitive};
use serde::{Deserialize, Serialize};

/// Generates all primes up to `limit` using the Sieve of Eratosthenes.
pub fn generate_primes(limit: usize) -> Vec<usize> {
    if limit < 2 {
        return Vec::new();
    }
    let mut is_prime = vec![true; limit + 1];
    is_prime[0] = false;
    is_prime[1] = false;
    let sqrt_limit = (limit as f64).sqrt() as usize;
    for i in 2..=sqrt_limit {
        if is_prime[i] {
            let mut j = i * i;
            while j <= limit {
                is_prime[j] = false;
                j += i;
            }
        }
    }
    is_prime
        .iter()
        .enumerate()
        .filter_map(|(idx, &p)| if p { Some(idx) } else { None })
        .collect()
}

/// Computes the modular inverse of `a` modulo `m` using the Extended Euclidean Algorithm.
/// Returns None if gcd(a, m) != 1.
pub fn mod_inverse(a: i64, m: i64) -> Option<i64> {
    let mut t = 0i64;
    let mut newt = 1i64;
    let mut r = m;
    let mut newr = a.rem_euclid(m);

    while newr != 0 {
        let quotient = r / newr;
        let temp_t = t - quotient * newt;
        t = newt;
        newt = temp_t;

        let temp_r = r - quotient * newr;
        r = newr;
        newr = temp_r;
    }

    if r > 1 {
        return None;
    }
    if t < 0 {
        t += m;
    }
    Some(t)
}

/// Computes the Jacobi symbol (a / n) for odd n > 0.
pub fn jacobi_symbol(mut a: BigInt, mut n: BigInt) -> i32 {
    if n <= BigInt::zero() || n.is_even() {
        return 0;
    }
    a = a.mod_floor(&n);
    let mut t = 1;
    while !a.is_zero() {
        while a.is_even() {
            a >>= 1;
            let r = (&n % 8).to_i32().unwrap();
            if r == 3 || r == 5 {
                t = -t;
            }
        }
        std::mem::swap(&mut a, &mut n);
        let a_mod4 = (&a % 4).to_i32().unwrap();
        let n_mod4 = (&n % 4).to_i32().unwrap();
        if a_mod4 == 3 && n_mod4 == 3 {
            t = -t;
        }
        a = a.mod_floor(&n);
    }
    if n == BigInt::one() {
        t
    } else {
        0
    }
}

/// Fast deterministic Miller-Rabin test for numbers up to 2^64.
pub fn is_prime_u64(n: u64) -> bool {
    if n < 2 {
        return false;
    }
    if n == 2 || n == 3 || n == 5 || n == 7 {
        return true;
    }
    if n % 2 == 0 || n % 3 == 0 || n % 5 == 0 || n % 7 == 0 {
        return false;
    }
    // Bases sufficient for deterministic testing up to 2^64
    // (Bester-Pomerance-Selfridge-Wagstaff / Jim Sinclair)
    let bases: &[u64] = if n < 2_152_302_898_747 {
        &[2, 3, 5, 7, 11]
    } else {
        &[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    };

    let s = (n - 1).trailing_zeros();
    let d = (n - 1) >> s;

    for &b in bases {
        if b >= n {
            break;
        }
        let mut x = mod_pow_u128(b as u128, d as u128, n as u128);
        if x == 1 || x == (n - 1) as u128 {
            continue;
        }
        let mut composite = true;
        for _ in 1..s {
            x = (x * x) % (n as u128);
            if x == (n - 1) as u128 {
                composite = false;
                break;
            }
        }
        if composite {
            return false;
        }
    }
    true
}

fn mod_pow_u128(mut base: u128, mut exp: u128, modulus: u128) -> u128 {
    let mut result = 1u128;
    base %= modulus;
    while exp > 0 {
        if exp % 2 == 1 {
            result = (result * base) % modulus;
        }
        base = (base * base) % modulus;
        exp >>= 1;
    }
    result
}

/// Multiprecision strong Miller-Rabin probable prime test.
pub fn is_probable_prime(n: &BigUint, bases: &[u64]) -> bool {
    if n < &BigUint::from(2u32) {
        return false;
    }
    if n == &BigUint::from(2u32) || n == &BigUint::from(3u32) {
        return true;
    }
    if n.is_even() {
        return false;
    }

    let n_minus_1 = n - 1u32;
    let s = n_minus_1.trailing_zeros().unwrap_or(0);
    let d = &n_minus_1 >> s;

    for &base_u64 in bases {
        let base = BigUint::from(base_u64);
        if &base >= n {
            continue;
        }
        let mut x = base.modpow(&d, n);
        if x.is_one() || x == n_minus_1 {
            continue;
        }

        let mut composite = true;
        for _ in 1..s {
            x = x.modpow(&BigUint::from(2u32), n);
            if x == n_minus_1 {
                composite = false;
                break;
            }
        }
        if composite {
            return false;
        }
    }
    true
}

/// Proth Primality Proof for B = k * 2^n + 1 (with k odd, k < 2^n).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProthProof {
    pub witness_a: u64,
    pub verified: bool,
}

/// Attempts to prove primality of B = k * 2^n + 1 using Proth's Theorem.
/// Returns Ok(ProthProof) if proven prime, Err(false) if composite, Err(true) if unresolved.
pub fn proth_prove(k: u64, n: u32, b_val: &BigUint) -> Result<ProthProof, bool> {
    if k % 2 == 0 {
        return Err(false); // k must be odd
    }
    if n < 64 && k >= (1u64 << n) {
        return Err(true); // Proth requires k < 2^n
    }

    let b_int = b_val.to_bigint().unwrap();
    let exp = (b_val - 1u32) / 2u32;
    let b_minus_1 = b_val - 1u32;

    // Small candidate witnesses
    let test_witnesses = [3u64, 5, 7, 10, 11, 13, 17, 19, 23, 29, 31];
    for &a in &test_witnesses {
        let jac = jacobi_symbol(BigInt::from(a), b_int.clone());
        if jac == -1 {
            // Euler criterion ensures this witness works if B is prime
            let power = BigUint::from(a).modpow(&exp, b_val);
            if power == b_minus_1 {
                return Ok(ProthProof {
                    witness_a: a,
                    verified: true,
                });
            } else {
                // If Jacobi is -1 and power != -1 mod B, B is unconditionally COMPOSITE!
                return Err(false);
            }
        }
    }

    // Fallback: check standard base 3
    let power = BigUint::from(3u32).modpow(&exp, b_val);
    if power == b_minus_1 {
        Ok(ProthProof {
            witness_a: 3,
            verified: true,
        })
    } else {
        Err(false)
    }
}

/// Lucas-Lehmer-Riesel (LLR) Primality Proof for A = k * 2^n - 1 (with k odd, k < 2^n).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LlrProof {
    pub p_param: u64,
    pub u0: String,
    pub verified: bool,
}

/// Attempts to prove primality of A = k * 2^n - 1 using the Lucas-Lehmer-Riesel test.
pub fn llr_prove(k: u64, n: u32, a_val: &BigUint) -> Result<LlrProof, bool> {
    if k % 2 == 0 {
        return Err(false);
    }
    if n < 64 && k >= (1u64 << n) {
        return Err(true);
    }
    if n < 2 {
        return Err(false);
    }

    // Determine starting value u0 via Riesel's criterion:
    // We seek P such that Jacobi(P - 2, A) = 1 and Jacobi(P + 2, A) = -1.
    let a_int = a_val.to_bigint().unwrap();
    let mut chosen_p: Option<u64> = None;

    for p_cand in [4u64, 3, 5, 6, 8, 9, 10, 12, 14, 15] {
        let j1 = jacobi_symbol(BigInt::from(p_cand - 2), a_int.clone());
        let j2 = jacobi_symbol(BigInt::from(p_cand + 2), a_int.clone());
        if j1 == 1 && j2 == -1 {
            chosen_p = Some(p_cand);
            break;
        }
    }

    let p = chosen_p.unwrap_or(4);

    // Compute u0 = V_k(P, 1) mod A
    // Lucas V-sequence: V_0 = 2, V_1 = P, V_{m+1} = P * V_m - V_{m-1}
    let mut v_prev = BigUint::from(2u32);
    let mut v_curr = BigUint::from(p);
    for _ in 1..k {
        let v_next = (&BigUint::from(p) * &v_curr + a_val - &v_prev) % a_val;
        v_prev = v_curr;
        v_curr = v_next;
    }
    let u0_val = v_curr;

    // Iterate u_{i+1} = (u_i^2 - 2) mod A for i = 0 .. n - 2
    let mut u = u0_val.clone();
    let two = BigUint::from(2u32);
    for _ in 0..(n - 2) {
        let u_sq = &u * &u;
        if u_sq < two {
            u = (&u_sq + a_val - &two) % a_val;
        } else {
            u = (u_sq - &two) % a_val;
        }
    }

    if u.is_zero() {
        Ok(LlrProof {
            p_param: p,
            u0: u0_val.to_str_radix(10),
            verified: true,
        })
    } else {
        Err(false) // Composite
    }
}
