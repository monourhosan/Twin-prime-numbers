# Phase 4 Test Report & CI Verification

**Report Date:** 2026-11-12  
**Environment:** Python 3.12.10 (AMD64), pytest 9.2.0, NumPy 2.5.4, gmpy2 2.3.2, SymPy 1.14.0  
**Test Suite:** `tests/`  

---

## 1. Test Execution Summary

Command executed:
```bash
python -m pytest -q
```

Output:
```text
................................                                         [100%]
32 passed in 1.10s
```

### Breakdown by Module

| Test Module | Tests | Status | Scope |
| :--- | :---: | :---: | :--- |
| `tests/test_cats.py` | 5 | PASS | Phase 1 CATS bounded and structured sieves, small prime twin detection |
| `tests/phase2/test_phase2.py` | 13 | PASS | Phase 2 CRT wheel, Montgomery Lucas ladder, Proth/LLR preconditions, checkpoints |
| `tests/phase3/test_phase3.py` | 14 | PASS | Phase 3 S1 vs S2 equivalence, window invariance, independent 2x2 matrix Lucas, adversarial certificate tamper rejection, stale lease recovery, CLI config precedence |

---

## 2. Independent Verification Suite

Command executed:
```bash
python scripts/phase3_independent_verify.py proofs/phase3 proofs/phase2
```

Output:
```text
Independent Strict Verification of 6 certificate(s)...
  [PASS] cert_k1183377_n1664.json
     + Proth primality verified for B = k*2^1664+1 with witness w=5
     + Riesel Jacobi conditions confirmed: (5-2/A)=1, (5+2/A)=-1
     + Initial u0 confirmed via independent 2x2 matrix powering
     + LLR sequence verified: u_{n-2} == 0 mod A (A is unconditionally prime)
     + artifact_sha256 verified: a01afe7c4aafbf3c073b4fc168b2fe9aaadb7dd62c2728cc53adebf89b174e29
  [PASS] cert_k15993_n672.json
     + Proth primality verified for B = k*2^672+1 with witness w=7
     + Riesel Jacobi conditions confirmed: (3-2/A)=1, (3+2/A)=-1
     + Initial u0 confirmed via independent 2x2 matrix powering
     + LLR sequence verified: u_{n-2} == 0 mod A (A is unconditionally prime)
     + artifact_sha256 verified: 4d8d6f2a2ac9ed96fb11a5bbe32c49dd7a89aeb2e96e4a26af8dab9922f974a0
  [PASS] cert_k254697_n1024.json
     + Proth primality verified for B = k*2^1024+1 with witness w=5
     + Riesel Jacobi conditions confirmed: (9-2/A)=1, (9+2/A)=-1
     + Initial u0 confirmed via independent 2x2 matrix powering
     + LLR sequence verified: u_{n-2} == 0 mod A (A is unconditionally prime)
     + artifact_sha256 verified: 80e4f72de9db900f926fe753849e802f1af9fc1cb41165a248a80457cd65d74d
  [PASS] cert_k12477_n330.json
     + Proth primality verified for B = k*2^330+1 with witness w=17
     + Riesel Jacobi conditions confirmed: (3-2/A)=1, (3+2/A)=-1
     + Initial u0 confirmed via independent 2x2 matrix powering
     + LLR sequence verified: u_{n-2} == 0 mod A (A is unconditionally prime)
     + artifact_sha256 verified: c31819fb41003486db1d22b78573fa5d30717678db79d9ba9f4123fa66b0e3c5
  [PASS] cert_k126747_n384.json
     + Proth primality verified for B = k*2^384+1 with witness w=5
     + Riesel Jacobi conditions confirmed: (5-2/A)=1, (5+2/A)=-1
     + Initial u0 confirmed via independent 2x2 matrix powering
     + LLR sequence verified: u_{n-2} == 0 mod A (A is unconditionally prime)
     + artifact_sha256 verified: 6af9484503a863d449c82090311f4988bac5dbfe0f0a8de5d9517247b88408fc
  [PASS] cert_k61347_n512.json
     + Proth primality verified for B = k*2^512+1 with witness w=5
     + Riesel Jacobi conditions confirmed: (5-2/A)=1, (5+2/A)=-1
     + Initial u0 confirmed via independent 2x2 matrix powering
     + LLR sequence verified: u_{n-2} == 0 mod A (A is unconditionally prime)
     + artifact_sha256 verified: f25b1f6f88bdab3588cc4b53c9c3d9857370c3ab7f9c96866e732b1856462c12

[SUCCESS] All certificates passed independent strict verification!
```

---

## 3. Adversarial Mutation & Tamper Resistance Results

| Injection Scenario | Target Field | Expected Outcome | Actual Result |
| :--- | :--- | :--- | :--- |
| Bitflip on $p_-$ decimal digit | `p_minus` | Detection & FAIL | REJECTED: Arithmetic mismatch detected |
| Altered Proth witness $w$ | `proof_plus.witness` | Non-congruence & FAIL | REJECTED: Proth theorem failure |
| Altered artifact SHA-256 | `artifact_sha256` | Checksum mismatch & FAIL | REJECTED: Checksum recalculation mismatch |
| Stale worker heartbeat | Task lease | Lease expiration & task reclaimed | PASS: Stale task successfully reassigned |
| Overriding CLI flag | `--config` vs default | Config values retained | PASS: Custom config preserved |
