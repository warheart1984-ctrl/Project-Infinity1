use crate::query::ContinuityEngine;
use crate::storage::ContinuityStore;
use crate::types::*;
use anyhow::{anyhow, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DecisionReconstruction {
    pub decision: ContinuityEvent,
    pub thread: ContinuityThread,
    pub discussion_events: Vec<ContinuityEvent>,
    pub architecture_events: Vec<ContinuityEvent>,
    pub governance_events: Vec<ContinuityEvent>,
    pub evidence_events: Vec<ContinuityEvent>,
    pub alternative_decisions: Vec<ContinuityEvent>,
    pub outcome_events: Vec<ContinuityEvent>,
}

pub struct ReconstructionEngine<S: ContinuityStore + 'static> {
    continuity: ContinuityEngine<S>,
}

impl<S: ContinuityStore> ReconstructionEngine<S> {
    pub fn new(continuity: ContinuityEngine<S>) -> Self {
        Self { continuity }
    }

    pub fn reconstruct_decision(&self, decision_id: EventId) -> Result<DecisionReconstruction> {
        let decision = self
            .continuity
            .get_event(decision_id)?
            .ok_or_else(|| anyhow!("Decision event not found"))?;

        if decision.event_type != EventType::Decision {
            return Err(anyhow!("Event is not a Decision"));
        }

        let thread = self
            .continuity
            .get_thread(decision.thread_id)?
            .ok_or_else(|| anyhow!("Thread not found"))?;

        let lineage_chain = self.continuity.get_lineage_chain(decision.id)?;

        let mut discussion_events = Vec::new();
        let mut architecture_events = Vec::new();
        let mut governance_events = Vec::new();
        let mut evidence_events = Vec::new();
        let mut alternative_decisions = Vec::new();
        let mut outcome_events = Vec::new();

        for ev in lineage_chain {
            if ev.id == decision.id {
                continue;
            }
            match ev.event_type {
                EventType::Architecture => architecture_events.push(ev),
                EventType::Governance => governance_events.push(ev),
                EventType::Evidence => evidence_events.push(ev),
                EventType::Decision => alternative_decisions.push(ev),
                EventType::Note => discussion_events.push(ev),
                _ => discussion_events.push(ev),
            }
        }

        let all_thread_events = self.continuity.list_events_for_thread(thread.id)?;
        for ev in all_thread_events {
            if ev.timestamp > decision.timestamp {
                outcome_events.push(ev);
            }
        }

        Ok(DecisionReconstruction {
            decision,
            thread,
            discussion_events,
            architecture_events,
            governance_events,
            evidence_events,
            alternative_decisions,
            outcome_events,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::storage::InMemoryStore;
    use serde_json::json;
    use std::sync::Arc;

    #[test]
    fn reconstruct_neomundi_decision() {
        let store = Arc::new(InMemoryStore::new());
        let continuity = ContinuityEngine::new(store);
        let recon = ReconstructionEngine::new(continuity.clone());

        let thread = continuity
            .create_thread(Some("NeoMundi Architecture Choice".into()), None)
            .unwrap();

        let note = continuity
            .append_event(
                thread.id,
                EventType::Note,
                json!({"text": "We need a governed world model for NeoMundi."}),
                vec![],
            )
            .unwrap();

        let evidence = continuity
            .append_event(
                thread.id,
                EventType::Evidence,
                json!({"source": "experiment-2026-06-19", "summary": "Un-governed agents drift."}),
                vec![note.id],
            )
            .unwrap();

        let arch = continuity
            .append_event(
                thread.id,
                EventType::Architecture,
                json!({"name": "NeoMundi v1", "pattern": "governed world model over FOS"}),
                vec![note.id, evidence.id],
            )
            .unwrap();

        let decision = continuity
            .append_event(
                thread.id,
                EventType::Decision,
                json!({
                    "title": "Adopt NeoMundi v1",
                    "rationale": "We need a governed world model integrated with FOS continuity.",
                    "chosen_architecture": arch.id,
                }),
                vec![arch.id, evidence.id],
            )
            .unwrap();

        let reconstruction = recon.reconstruct_decision(decision.id).unwrap();

        assert_eq!(reconstruction.decision.id, decision.id);
        assert!(!reconstruction.discussion_events.is_empty());
        assert_eq!(reconstruction.architecture_events.len(), 1);
        assert_eq!(reconstruction.evidence_events.len(), 1);
        assert!(reconstruction.alternative_decisions.is_empty());
    }
}
