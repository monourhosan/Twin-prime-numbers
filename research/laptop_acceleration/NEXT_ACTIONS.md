# Next Recommended Actions: Laptop Twin-Prime Search

**Campaign Target:** 2,000+ Digit Twin-Prime Pair Search (`laptop_2k_exploration`)  
**Date:** 2026-11-13  

---

## 1. Immediate Execution Steps

1. **Launch Sustained Background Campaign:**
   Execute the unattended launcher to begin processing 2,000+ digit candidates on the hybrid engine:
   ```cmd
   scripts\run_laptop_campaign.bat
   ```
   Or via PowerShell:
   ```powershell
   python -m src.phase4 search --config configs/laptop_i5_10210u_mx250.json
   ```

2. **Monitor Live Telemetry:**
   Periodically check the campaign's progress, candidate testing rate, and any sieve survivors:
   ```powershell
   python -m src.phase4 status --campaign laptop_2k_exploration
   ```

3. **Audit Search Coverage:**
   Verify that work units remain gap-free and properly recorded in the SQLite WAL ledger:
   ```powershell
   python -m src.phase4 coverage-audit --campaign laptop_2k_exploration
   ```

---

## 2. When a New 2,000+ Digit Pair is Found

1. The search engine will automatically:
   - Output proof metrics to terminal and log files.
   - Save the raw Schema 4.0 proof payload to `proofs/phase4/cert_k<k>_n<n>.json`.
   - Run the strict independent verifier in a separate subprocess.
   - Generate the machine-readable attestation in `proofs/phase4/attestations/attest_<sha[:16]>.json`.
   - Commit the discovery to the SQLite database.
2. Update `proofs/phase4/sha256sums.txt`.
3. Generate a formal discovery report and prepare submission for prime database novelty review.
