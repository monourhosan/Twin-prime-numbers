"""
Phase 5: Smooth-Center Certificate-Aware Search (SCCA) Engine.
Rigorously discovers and certifies twin-prime pairs (A, B) = (C - 1, C + 1)
with smooth center C = F * t, using Pocklington (N-1) and Morrison (N+1) theorems.
"""

__version__ = "5.0.0"
__all__ = [
    "candidates",
    "crt_walker",
    "primality",
    "certificate",
    "storage",
    "scheduler",
]
