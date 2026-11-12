"""
Generates publication-quality charts for paper/phase3/phase3_twin_prime_research_paper.md
from real benchmark measurements and certified discovery data.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "paper" / "phase3" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# 1. Sieve Strategy Speedup (S1 & S2 vs S0)
exp_labels = ["n=672\n(202d)", "n=1024\n(308d)", "n=1664\n(500d)"]
s1_speedups = [14.6, 8.1, 9.3]
s2_speedups = [0.9, 1.6, 1.9]

x = np.arange(len(exp_labels))
width = 0.35

fig, ax = plt.subplots(figsize=(7.5, 4.5))
rects1 = ax.bar(x - width/2, s1_speedups, width, label="S1 (Vectorized Segmented Bitset)", color="#1f77b4", edgecolor="black")
rects2 = ax.bar(x + width/2, s2_speedups, width, label="S2 (Hybrid Strided + Sparse)", color="#ff7f0e", edgecolor="black")

ax.set_ylabel("Speedup Factor vs S0 Baseline (x)")
ax.set_title("Sieving Speedup across Target Regimes (Cutoff Q=50,000)")
ax.set_xticks(x)
ax.set_xticklabels(exp_labels)
ax.legend()
ax.grid(axis='y', linestyle='--', alpha=0.7)

for rect in rects1:
    h = rect.get_height()
    ax.text(rect.get_x() + rect.get_width()/2., h + 0.3, f"{h:.1f}x", ha='center', va='bottom', fontweight='bold', fontsize=9)
for rect in rects2:
    h = rect.get_height()
    ax.text(rect.get_x() + rect.get_width()/2., h + 0.3, f"{h:.1f}x", ha='center', va='bottom', fontsize=9)

ax.set_ylim(0, 18)
plt.tight_layout()
plt.savefig(FIG_DIR / "sieve_strategy_speedup.png", dpi=200)
plt.close()

# 2. Sieve Throughput Comparison (cands/sec)
depths = ["Q=10k", "Q=50k", "Q=100k"]
s0_rates = [806451, 200000, 123152]
s1_rates = [50000000, 1612903, 632911]

fig, ax = plt.subplots(figsize=(7.5, 4.5))
ax.plot(depths, s1_rates, 'b-o', linewidth=2.5, label="S1 Vectorized Bitset (cands/s)")
ax.plot(depths, s0_rates, 'r--s', linewidth=2, label="S0 Phase 2 Baseline (cands/s)")
ax.set_yscale("log")
ax.set_ylabel("Candidate Throughput (cands/sec, log scale)")
ax.set_title("Throughput vs Sieve Depth (n=1024, 308 digits)")
ax.grid(True, which="both", ls="--", alpha=0.5)
ax.legend()
plt.tight_layout()
plt.savefig(FIG_DIR / "sieve_throughput_comparison.png", dpi=200)
plt.close()

# 3. Discovery Scaling: Phase 1 -> Phase 2 -> Phase 3
milestones = [
    ("Phase 1 Baseline\nk=4107, n=100", 34, "#7f7f7f"),
    ("Phase 2\nk=12477, n=330", 104, "#aec7e8"),
    ("Phase 2\nk=126747, n=384", 121, "#aec7e8"),
    ("Phase 2\nk=61347, n=512", 159, "#aec7e8"),
    ("Phase 3 Pilot\nk=15993, n=672", 207, "#2ca02c"),
    ("Phase 3 Primary\nk=254697, n=1024", 314, "#1f77b4"),
    ("Phase 3 Stretch\nk=1183377, n=1664", 507, "#d62728"),
]
labels = [m[0] for m in milestones]
digits = [m[1] for m in milestones]
colors = [m[2] for m in milestones]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(labels, digits, color=colors, edgecolor="black", width=0.6)
ax.set_ylabel("Decimal Digits per Member")
ax.set_title("Evolution of Certified Twin-Prime Discoveries in this Repository")
ax.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 8, f"{yval}d", ha='center', va='bottom', fontweight='bold', fontsize=9.5)

ax.set_ylim(0, 560)
plt.xticks(rotation=15, ha='right')
plt.tight_layout()
plt.savefig(FIG_DIR / "discovery_progression_digits.png", dpi=200)
plt.close()

print("[OK] Generated 3 publication figures in paper/phase3/figures/")
