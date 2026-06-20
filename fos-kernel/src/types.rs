use serde::{Deserialize, Serialize};

pub type Id = String;
pub type Version = String;
pub type ContinuityThreadId = String;
pub type EvidenceRef = String;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "PascalCase")]
pub enum MemoryType {
    Concept,
    Pattern,
    Invariant,
    Architecture,
    GovernanceContract,
    Decision,
    Evidence,
    ContinuityThread,
    SystemModel,
    Blueprint,
    FieldDefinition,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MemoryObject {
    pub id: Id,
    pub mtype: MemoryType,
    pub definition: String,
    pub evidence_refs: Vec<EvidenceRef>,
    pub lineage: Vec<Id>,
    pub version: Version,
    pub continuity_thread: ContinuityThreadId,
}
