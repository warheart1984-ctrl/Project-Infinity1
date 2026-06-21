use crate::types::*;
use serde::{Deserialize, Serialize};

/// Higher-level typed views over raw events.
/// These are *projections* on top of ContinuityEvent.

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Concept {
    pub id: EventId,
    pub thread_id: ThreadId,
    pub name: String,
    pub definition: String,
    pub evidence_refs: Vec<EventId>,
    pub lineage: Vec<EventId>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ArchitectureBlueprint {
    pub id: EventId,
    pub thread_id: ThreadId,
    pub name: String,
    pub version: String,
    pub definition: String,
    pub invariants: Vec<String>,
    pub components: Vec<String>,
    pub evidence_refs: Vec<EventId>,
    pub lineage: Vec<EventId>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct GovernanceContract {
    pub id: EventId,
    pub thread_id: ThreadId,
    pub name: String,
    pub authority_scope: String,
    pub invariants: Vec<String>,
    pub constraints: Vec<String>,
    pub evidence_refs: Vec<EventId>,
    pub lineage: Vec<EventId>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Decision {
    pub id: EventId,
    pub thread_id: ThreadId,
    pub title: String,
    pub rationale: String,
    pub chosen_architecture: Option<EventId>,
    pub alternatives: Vec<EventId>,
    pub evidence_refs: Vec<EventId>,
    pub governance_refs: Vec<EventId>,
    pub outcome_summary: Option<String>,
    pub lineage: Vec<EventId>,
}
