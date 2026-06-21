use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

pub type ThreadId = Uuid;
pub type EventId = Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(rename_all = "PascalCase")]
pub enum EventType {
    Concept,
    Invariant,
    Architecture,
    Governance,
    Decision,
    Evidence,
    Note,
    Custom(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContinuityThread {
    pub id: ThreadId,
    pub parent: Option<ThreadId>,
    pub label: Option<String>,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContinuityEvent {
    pub id: EventId,
    pub thread_id: ThreadId,
    pub event_type: EventType,
    pub payload: serde_json::Value,
    pub timestamp: DateTime<Utc>,
    pub lineage: Vec<EventId>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct MemoryObjectRef {
    pub event_id: EventId,
    pub event_type: EventType,
}
