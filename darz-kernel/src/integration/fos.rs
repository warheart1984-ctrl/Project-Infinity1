//! DAR-Z execution → FOS continuity substrate (shared JSONL authority).

use std::path::Path;

use anyhow::Result;
use civilization_stack::{EventType, JsonlStore};
use serde_json::json;

use crate::hash::hash_to_hex;
use crate::types::{ExecutionDecision, TrajectoryMessage};

pub const DEFAULT_DARZ_THREAD: &str = "dar-z";

#[derive(Debug, Clone)]
pub struct DarzContinuityCoupling {
    store: JsonlStore,
    thread_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CouplingRecord {
    pub evidence_event_id: String,
    pub decision_event_id: String,
}

impl DarzContinuityCoupling {
    pub fn open(path: impl AsRef<Path>, thread_id: impl Into<String>) -> Result<Self> {
        Ok(Self {
            store: JsonlStore::new(path)?,
            thread_id: thread_id.into(),
        })
    }

    pub fn in_memory_dir(dir: impl AsRef<Path>, thread_id: impl Into<String>) -> Result<Self> {
        let path = dir.as_ref().join("continuity.jsonl");
        Self::open(path, thread_id)
    }

    pub fn store(&self) -> &JsonlStore {
        &self.store
    }

    pub fn thread_id(&self) -> &str {
        &self.thread_id
    }

    /// After kernel evaluation, append Evidence + Decision continuity events.
    pub fn record_evaluation(
        &self,
        msg: &TrajectoryMessage,
        decision: &ExecutionDecision,
        lineage: &[String],
    ) -> Result<CouplingRecord> {
        self.store.ensure_thread(&self.thread_id, None)?;

        let (allowed, reasons, replay_hash, regime_id, source_message_id) = match decision {
            ExecutionDecision::Execute(receipt) => (
                true,
                Vec::<String>::new(),
                receipt.replay_hash,
                receipt.regime_id.clone(),
                receipt.source_message_id.clone(),
            ),
            ExecutionDecision::Block(receipt) => (
                false,
                receipt.reasons.clone(),
                receipt.replay_hash,
                receipt.regime_id.clone(),
                receipt.source_message_id.clone(),
            ),
        };

        let evidence = self.store.append_event(
            &self.thread_id,
            EventType::Evidence,
            json!({
                "source": "darz-kernel",
                "subsystem": "execution-audit",
                "trajectory_message_id": msg.id,
                "origin": msg.origin,
                "lts_state": msg.lts_state,
                "replay_hash": hash_to_hex(replay_hash),
                "regime_id": regime_id,
                "allowed": allowed,
                "reasons": reasons,
            }),
            lineage.to_vec(),
            None,
        )?;

        let decision_lineage = {
            let mut chain = lineage.to_vec();
            chain.push(evidence.event_id.clone());
            chain
        };

        let decision_event = self.store.append_event(
            &self.thread_id,
            EventType::Decision,
            json!({
                "title": if allowed {
                    format!("DAR-Z Execute: {}", source_message_id)
                } else {
                    format!("DAR-Z Block: {}", source_message_id)
                },
                "rationale": if reasons.is_empty() {
                    "kernel execution admitted".to_string()
                } else {
                    reasons.join("; ")
                },
                "source_message_id": source_message_id,
                "allowed": allowed,
                "replay_hash": hash_to_hex(replay_hash),
                "evidence_refs": [evidence.event_id.clone()],
            }),
            decision_lineage,
            None,
        )?;

        Ok(CouplingRecord {
            evidence_event_id: evidence.event_id,
            decision_event_id: decision_event.event_id,
        })
    }

    /// Export concept/architecture/governance events for kernel policy grounding.
    pub fn export_grounding_events(&self) -> Vec<civilization_stack::ContinuityEventWire> {
        self.store
            .list_events_for_thread(&self.thread_id)
            .into_iter()
            .filter(|event| {
                matches!(
                    event.event_type.as_str(),
                    "Concept" | "Invariant" | "Architecture" | "Governance"
                )
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{DefaultKernelValidator, KernelPolicy, KernelValidator};

    #[test]
    fn evaluation_appends_evidence_and_decision_to_jsonl() {
        let dir = std::env::temp_dir().join(format!("darz-fos-{}", uuid::Uuid::new_v4()));
        std::fs::create_dir_all(&dir).unwrap();
        let coupling = DarzContinuityCoupling::in_memory_dir(&dir, "dar-z").unwrap();

        let msg = TrajectoryMessage::new(
            "proposal-001",
            "aais",
            "stable",
            "history",
            [("intent", "observe"), ("domain", "ai")],
        );
        let decision = DefaultKernelValidator::new(KernelPolicy::default()).evaluate(&msg);
        let record = coupling.record_evaluation(&msg, &decision, &[]).unwrap();

        assert!(!record.evidence_event_id.is_empty());
        assert!(!record.decision_event_id.is_empty());
        assert!(coupling.store().get_event(&record.evidence_event_id).is_some());

        // Reload from disk — shared authority with Python FOS
        let path = dir.join("continuity.jsonl");
        let reloaded = JsonlStore::new(path).unwrap();
        assert_eq!(reloaded.list_events_for_thread("dar-z").len(), 2);
    }
}
