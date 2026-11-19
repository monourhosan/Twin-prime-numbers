"""Phase 11 Campaign CLI Runner.

Usage:
  python scripts/phase11/run_campaign.py --stage sanity
  python scripts/phase11/run_campaign.py --stage discovery --anchor-y 5 --t-start 1 --t-end 1000 --prime-limit 5000
"""

import argparse
import sys
from pathlib import Path

# Ensure repository root is in sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.phase11.campaign import CampaignOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 11 Twin-Prime Discovery Campaign CLI")
    parser.add_argument(
        "--stage",
        choices=["sanity", "density", "optimize", "discovery"],
        default="sanity",
        help="Campaign execution stage",
    )
    parser.add_argument("--anchor-y", type=int, default=3, help="Primorial anchor bound y >= 3")
    parser.add_argument("--t-start", type=int, default=1, help="Starting multiplier t")
    parser.add_argument("--t-end", type=int, default=100, help="Ending multiplier t")
    parser.add_argument("--prime-limit", "--sieve-depth", type=int, default=1000, help="Sieve prime depth")
    parser.add_argument("--batch-size", type=int, default=200, help="Work unit batch size")
    parser.add_argument("--resume", action="store_true", help="Resume from existing checkpoint")
    parser.add_argument("--output-dir", type=Path, default=Path("runs/phase11"), help="Checkpoint directory")
    parser.add_argument("--cpu-only", action="store_true", help="Enforce CPU-only mode")
    parser.add_argument("--enforce-guardrails", action="store_true", help="Enforce strict RAM pause")

    args = parser.parse_args()

    # Stage defaults configuration
    if args.stage == "sanity":
        y = 3
        t_start, t_end = 1, 50
        depth = 100
        run_id = "stage1_sanity"
    elif args.stage == "density":
        y = args.anchor_y or 5
        t_start, t_end = 1, 500
        depth = 500
        run_id = "stage2_density"
    elif args.stage == "optimize":
        y = args.anchor_y or 5
        t_start, t_end = 1, 1000
        depth = 2000
        run_id = "stage3_optimize"
    else:  # discovery
        y = args.anchor_y
        t_start, t_end = args.t_start, args.t_end
        depth = args.prime_limit
        run_id = f"stage4_discovery_y{y}_t{t_start}_{t_end}"

    print(f"=== Starting Phase 11 Campaign: Stage '{args.stage}' ===")
    print(f"Run ID: {run_id} | Anchor y: {y} | Multiplier range: [{t_start}, {t_end}] | Sieve depth: {depth}")

    orchestrator = CampaignOrchestrator(
        run_id=run_id,
        anchor_y=y,
        t_start=t_start,
        t_end=t_end,
        sieve_depth=depth,
        batch_size=args.batch_size,
        output_dir=args.output_dir,
        stop_on_first_discovery=(args.stage == "discovery"),
        enforce_ram_guardrail=args.enforce_guardrails,
    )

    if args.resume:
        loaded = orchestrator.load_checkpoint_if_exists()
        print(f"Resumption requested: Loaded existing checkpoint = {loaded}")

    result = orchestrator.execute()

    print("\n=== Campaign Completed ===")
    print(f"Survivors identified: {result['survivors_found']}")
    print(f"Verified twin pairs discovered: {len(result['discoveries'])}")
    for disc in result["discoveries"]:
        print(f" -> Pair: y={disc['anchor_y']}, t={disc['multiplier_t']}, digits={disc['digits']}")
        print(f"    Lower: {disc['lower_prime']}")
        print(f"    Upper: {disc['upper_prime']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
