//! Primality Certificate serialization, checksum hashing, and verification.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::File;
use std::io::{self, Write};
use std::path::Path;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TwinPrimeCertificate {
    pub certificate_id: String,
    pub timestamp_utc: String,
    pub engine_version: String,
    pub pair_type: String,
    pub digits: usize,
    pub k: Option<u64>,
    pub n: Option<u32>,
    pub center_m: String,
    pub p_minus: String,
    pub p_plus: String,
    pub p_plus_proof: Option<ProofDetail>,
    pub p_minus_proof: Option<ProofDetail>,
    pub proof_status: String, // "PROVEN_PRIME_PAIR", "STRONG_PRP_PAIR", "UNRESOLVED"
    pub sha256_hash: String,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProofDetail {
    pub method: String, // "PROTH_THEOREM", "LUCAS_LEHMER_RIESEL", "MILLER_RABIN_DETERMINISTIC"
    pub witness: u64,
    pub condition_checked: String,
    pub passed: bool,
}

impl TwinPrimeCertificate {
    pub fn new_structured(
        k: u64,
        n: u32,
        p_minus_str: String,
        p_plus_str: String,
        digits: usize,
        proth_witness: Option<u64>,
        llr_witness: Option<u64>,
        is_proven: bool,
    ) -> Self {
        let p_plus_proof = proth_witness.map(|w| ProofDetail {
            method: "PROTH_THEOREM".to_string(),
            witness: w,
            condition_checked: format!("w^((B-1)/2) == -1 (mod B), with w={}, k={}, n={}", w, k, n),
            passed: true,
        });

        let p_minus_proof = llr_witness.map(|w| ProofDetail {
            method: "LUCAS_LEHMER_RIESEL".to_string(),
            witness: w,
            condition_checked: format!("u_{{n-2}} == 0 (mod A), P={}, k={}, n={}", w, k, n),
            passed: true,
        });

        let proof_status = if is_proven {
            "PROVEN_PRIME_PAIR".to_string()
        } else {
            "STRONG_PRP_PAIR".to_string()
        };

        let now = chrono::Utc::now().to_rfc3339();
        let mut cert = Self {
            certificate_id: format!("CATS-TWIN-k{}-n{}-{}", k, n, &now[..10]),
            timestamp_utc: now,
            engine_version: "CATS-Engine-1.0.0 (Rust/num-bigint)".to_string(),
            pair_type: "Structured: k * 2^n +/- 1".to_string(),
            digits,
            k: Some(k),
            n: Some(n),
            center_m: format!("{} * 2^{}", k, n),
            p_minus: p_minus_str,
            p_plus: p_plus_str,
            p_plus_proof,
            p_minus_proof,
            proof_status,
            sha256_hash: String::new(),
        };

        cert.sha256_hash = cert.compute_hash();
        cert
    }

    pub fn compute_hash(&self) -> String {
        let mut hasher = Sha256::new();
        hasher.update(self.certificate_id.as_bytes());
        hasher.update(self.pair_type.as_bytes());
        hasher.update(self.p_minus.as_bytes());
        hasher.update(self.p_plus.as_bytes());
        hasher.update(self.proof_status.as_bytes());
        if let Some(ref p) = self.p_plus_proof {
            hasher.update(p.condition_checked.as_bytes());
        }
        if let Some(ref p) = self.p_minus_proof {
            hasher.update(p.condition_checked.as_bytes());
        }
        format!("{:x}", hasher.finalize())
    }

    pub fn save_to_file<P: AsRef<Path>>(&self, path: P) -> io::Result<()> {
        let json = serde_json::to_string_pretty(self)
            .map_err(|e| io::Error::new(io::ErrorKind::Other, e))?;
        let mut file = File::create(path)?;
        file.write_all(json.as_bytes())?;
        Ok(())
    }
}
