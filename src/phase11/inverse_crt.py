"""Phase 11 CRT-Kernel Inverse Sieve Pre-Filtering.

Constructs filter modulus M_filter = prod_{q in Q} q and survivor residue classes t_0
such that 100% of candidates t = t_0 + j * M_filter survive all prime moduli in Q.
"""

import math


def find_roots_mod_q(q: int) -> tuple[list[int], list[int]]:
    """Finds roots in [0, q-1] of B(x) = 12x^5 + 6x^3 + 1 = 0 mod q

    and derives roots of A(x) = 12x^5 + 6x^3 - 1 = 0 mod q via root-negation symmetry:
      r_A = (q - r_B) mod q.
    """
    if q < 2 or q in (2, 3):
        return [], []
    roots_B = []
    for r in range(q):
        val = (12 * pow(r, 5, q) + 6 * pow(r, 3, q) + 1) % q
        if val == 0:
            roots_B.append(r)
    # Root negation symmetry: r_A = (q - r_B) % q
    roots_A = sorted([(q - r) % q for r in roots_B])
    return roots_A, sorted(roots_B)


def solve_crt(residues: list[int], moduli: list[int]) -> int:
    """Solves system t = r_i mod m_i for pairwise coprime moduli.

    Returns unique solution t_0 in [0, M - 1] where M = prod(moduli).
    """
    M = math.prod(moduli)
    x = 0
    for r, m in zip(residues, moduli):
        Mi = M // m
        inv = pow(Mi, -1, m)
        x = (x + r * Mi * inv) % M
    return x


class CRTFilter:
    """Computes CRT filter parameters and generates pre-filtered progressions."""

    def __init__(self, anchor_y: int, basis_primes: list[int]):
        self.anchor_y = anchor_y
        self.basis_primes = sorted([q for q in basis_primes if q > anchor_y])
        self.M_filter = math.prod(self.basis_primes) if self.basis_primes else 1
        self.admissible_per_q: dict[int, list[int]] = {}
        self._precompute_admissible_residues()

    def _precompute_admissible_residues(self) -> None:
        from .math_model import compute_primorial
        Sy = compute_primorial(self.anchor_y)
        for q in self.basis_primes:
            roots_A, roots_B = find_roots_mod_q(q)
            forbidden_x = set(roots_A) | set(roots_B)
            inv_Sy = pow(Sy % q, -1, q)
            forbidden_t = {(r * inv_Sy) % q for r in forbidden_x}
            admissible_t = [r for r in range(q) if r not in forbidden_t]
            self.admissible_per_q[q] = admissible_t

    def get_admissible_t0_residues(self, limit_classes: int = 50) -> list[int]:
        """Computes combined admissible residue classes modulo M_filter via CRT."""
        if not self.basis_primes:
            return [1]
        classes: list[int] = []

        def backtrack(idx: int, current_residues: list[int]) -> None:
            if len(classes) >= limit_classes:
                return
            if idx == len(self.basis_primes):
                t0 = solve_crt(current_residues, self.basis_primes)
                classes.append(t0)
                return
            q = self.basis_primes[idx]
            for r in self.admissible_per_q[q]:
                backtrack(idx + 1, current_residues + [r])
                if len(classes) >= limit_classes:
                    break

        backtrack(0, [])
        return sorted(classes)

    def generate_candidate_stream(
        self,
        t_start: int,
        t_end: int,
        odd_only: bool = True
    ) -> list[int]:
        """Generates candidate t in [t_start, t_end] pre-filtered against basis primes."""
        classes = self.get_admissible_t0_residues()
        candidates: set[int] = set()
        M = self.M_filter
        for t0 in classes:
            # Step along t0 + j * M
            first_j = max(0, (t_start - t0 + M - 1) // M)
            j = first_j
            while True:
                t = t0 + j * M
                if t > t_end:
                    break
                if t >= t_start and (not odd_only or (t % 2 == 1)):
                    candidates.add(t)
                j += 1
        return sorted(candidates)
