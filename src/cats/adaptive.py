"""
Adaptive Sieve Depth (ASD) cost model and scheduler.
"""

def estimate_optimal_sieve_depth(n: int, k_count: int) -> int:
    """
    Computes optimal sieve depth Q* balancing modular sieve cost against
    big-integer Miller-Rabin and deterministic primality proof costs.
    """
    bit_length = float(n)
    # Scaling model: candidate size scales with bit_length,
    # multiplication scales as O(bits^1.6), modular inversion as O(1).
    base_q = 5_000.0 * max(1.0, bit_length / 100.0) ** 1.35
    q_clamped = int(max(1_000, min(2_000_000, base_q)))
    if k_count > 100_000:
        return min(5_000_000, q_clamped * 2)
    return q_clamped
