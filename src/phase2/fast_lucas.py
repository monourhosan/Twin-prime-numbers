"""
Fast O(log k) Lucas sequence computation for LLR primality proofs.
"""

def lucas_v_fast(k: int, P: int, m: int) -> int:
    """
    Computes V_k(P, 1) mod m in O(log k) modular multiplications
    using the Montgomery doubling ladder for Lucas sequences.

    Recurrence relations:
      V_{2m}   = V_m^2 - 2 (mod m)
      V_{2m+1} = V_m * V_{m+1} - P (mod m)
    """
    if k == 0:
        return 2 % m
    if k == 1:
        return P % m

    # Ladder state: (v0, v1) representing (V_j, V_{j+1})
    v0 = 2 % m
    v1 = P % m

    # Process bits of k from MSB to LSB
    bits = bin(k)[2:]
    for b in bits:
        if b == '0':
            v1 = (v0 * v1 - P) % m
            v0 = (v0 * v0 - 2) % m
        else:
            v0 = (v0 * v1 - P) % m
            v1 = (v1 * v1 - 2) % m
    return v0

def lucas_v_linear(k: int, P: int, m: int) -> int:
    """
    Reference O(k) linear recurrence calculation of V_k(P, 1) mod m.
    Used exclusively as an audit oracle for regression testing.
    """
    if k == 0:
        return 2 % m
    if k == 1:
        return P % m
    v_prev = 2 % m
    v_curr = P % m
    for _ in range(1, k):
        v_next = (P * v_curr - v_prev) % m
        v_prev = v_curr
        v_curr = v_next
    return v_curr
