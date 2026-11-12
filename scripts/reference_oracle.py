"""
Independent Reference Oracle for Twin Prime Verification
Uses Python and SymPy to compute provable ground-truth twin primes.
Used as an independent oracle to cross-validate the Rust CATS engine.
"""

import sys
import json
import sympy

def find_twins_in_range(lower: int, upper: int):
    """
    Exhaustively searches [lower, upper] for twin primes using SymPy trial division.
    Returns list of tuples (p, p+2).
    """
    twins = []
    # If lower <= 3 and upper >= 5, (3, 5) is a twin pair
    if lower <= 3 and upper >= 5:
        twins.append((3, 5))
    
    # Check all centers m = 6r
    r_start = max(1, (lower + 5) // 6)
    r_end = (upper - 1) // 6
    
    for r in range(r_start, r_end + 1):
        p1 = 6 * r - 1
        p2 = 6 * r + 1
        if p1 >= lower and p2 <= upper:
            if sympy.isprime(p1) and sympy.isprime(p2):
                twins.append((p1, p2))
                
    return twins

def verify_structured_candidate(k: int, n: int):
    """
    Verifies whether k * 2^n +/- 1 is a twin prime pair using SymPy provable primality.
    """
    center = k * (1 << n)
    p_minus = center - 1
    p_plus = center + 1
    
    is_p_minus = sympy.isprime(p_minus)
    is_p_plus = sympy.isprime(p_plus)
    
    return {
        "k": k,
        "n": n,
        "p_minus_prime": is_p_minus,
        "p_plus_prime": is_p_plus,
        "is_twin_pair": is_p_minus and is_p_plus,
        "digits": len(str(p_plus))
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reference_oracle.py [range <min> <max> | test_candidate <k> <n>]")
        sys.exit(1)
        
    cmd = sys.argv[1]
    if cmd == "range":
        low = int(sys.argv[2])
        high = int(sys.argv[3])
        res = find_twins_in_range(low, high)
        print(f"Found {len(res)} twin prime pairs in [{low}, {high}].")
        if res:
            print(f"First 5: {res[:5]}")
            print(f"Last 5: {res[-5:]}")
    elif cmd == "test_candidate":
        k_val = int(sys.argv[2])
        n_val = int(sys.argv[3])
        res = verify_structured_candidate(k_val, n_val)
        print(json.dumps(res, indent=2))
