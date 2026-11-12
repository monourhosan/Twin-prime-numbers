"""
Generates publication-quality charts for paper/phase2_new_twin_prime_discovery.md
from real benchmark data and discovery records.
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
FIG_DIR = ROOT / "paper" / "phase2_figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# 1. Lucas Sequence Speedup Plot
ks = [100, 1000, 10000, 50000, 200000]
linear_times_ms = [0.001, 0.001, 0.001, 16.0, 31.0]
fast_times_ms = [0.001, 0.001, 0.001, 0.001, 0.001]
speedups = [1.0, 1.0, 1.0, 16000.0, 31000.0]

fig, ax1 = plt.subplots(figsize=(7, 4.5))
ax1.plot(ks, linear_times_ms, 'r-o', label="Naive O(k) linear loop (ms)")
ax1.plot(ks, fast_times_ms, 'b-s', label="Montgomery Ladder O(log k) (ms)")
ax1.set_xlabel("Multiplier k")
ax1.set_ylabel("Execution Time (ms)")
ax1.set_xscale("log")
ax1.set_yscale("log")
ax1.grid(True, which="both", ls="--", alpha=0.5)
ax1.set_title("Lucas Sequence Initialization: O(log k) vs O(k)")
ax1.legend(loc="upper left")
plt.tight_layout()
plt.savefig(FIG_DIR / "lucas_speedup.png", dpi=200)
plt.close()

# 2. CRT Wheel Rejection Plot
wheel_names = ["None\n(all odd)", "{3}", "{3,5}", "{3,5,7}", "{3,5,7,11}", "CRT Wheel\n{3,5,7,11,13}"]
rejection_pcts = [0.0, 66.67, 80.0, 85.72, 88.31, 90.11]
survivor_pcts = [100.0, 33.33, 20.0, 14.28, 11.69, 9.89]

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.bar(wheel_names, rejection_pcts, color="#2b5c8f", edgecolor="black", alpha=0.85)
ax.set_ylabel("Candidates Eliminated (%)")
ax.set_ylim(0, 100)
ax.grid(axis='y', linestyle='--', alpha=0.7)
ax.set_title("CRT Wheel Prefiltering: Cumulative Candidate Rejection (%)")

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f"{yval:.1f}%", ha='center', va='bottom', fontweight='bold', fontsize=9)

plt.tight_layout()
plt.savefig(FIG_DIR / "crt_wheel_rejection.png", dpi=200)
plt.close()

# 3. Sieve Depth Tradeoff
depths = [5000, 10000, 25000, 50000, 100000]
survivor_pct = [1.160, 0.990, 0.814, 0.720, 0.654]
times_ms = [62.0, 78.0, 141.0, 234.0, 344.0]

fig, ax1 = plt.subplots(figsize=(7.5, 4.5))
color = 'tab:blue'
ax1.set_xlabel('Sieve Depth Cutoff Q')
ax1.set_ylabel('Candidate Survivor Rate (%)', color=color)
ax1.plot(depths, survivor_pct, color=color, marker='o', linewidth=2)
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True, ls='--', alpha=0.5)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('Sieve Latency per 100k Window (ms)', color=color)
ax2.plot(depths, times_ms, color=color, marker='s', linestyle='--', linewidth=2)
ax2.tick_params(axis='y', labelcolor=color)

plt.title("Sieve Depth Optimization: Density Reduction vs Compute Latency")
plt.tight_layout()
plt.savefig(FIG_DIR / "sieve_depth_tradeoff.png", dpi=200)
plt.close()

# 4. Discovery Scale Comparison (Digits)
records = [
    ("Phase 1 Baseline\nk=4107, n=100", 34, "#7f7f7f"),
    ("Phase 2 Find #1\nk=12477, n=330", 104, "#1f77b4"),
    ("Phase 2 Find #2\nk=126747, n=384", 121, "#2ca02c"),
    ("Phase 2 Find #3\nk=61347, n=512", 159, "#d62728"),
]
labels = [r[0] for r in records]
digits = [r[1] for r in records]
colors = [r[2] for r in records]

fig, ax = plt.subplots(figsize=(8.5, 4.5))
bars = ax.bar(labels, digits, color=colors, edgecolor="black", width=0.55)
ax.set_ylabel("Decimal Digits per Member")
ax.set_title("Twin-Prime Discovery Scale: Phase 1 Baseline vs Phase 2 Breakthroughs")
ax.grid(axis='y', linestyle='--', alpha=0.7)

for bar in bars:
    yval = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2.0, yval + 3, f"{yval} digits", ha='center', va='bottom', fontweight='bold')

ax.set_ylim(0, 185)
plt.tight_layout()
plt.savefig(FIG_DIR / "digit_scaling_discoveries.png", dpi=200)
plt.close()

print("[OK] Generated 4 figures in paper/phase2_figures/")
