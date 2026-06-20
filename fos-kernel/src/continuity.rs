use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::types::{ContinuityThreadId, Id};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContinuityEvent {
    pub thread: ContinuityThreadId,
    pub event_id: Id,
    pub kind: String,
    pub payload: serde_json::Value,
}

pub struct ContinuityEngine;

impl ContinuityEngine {
    pub fn emit(
        kind: &str,
        thread: &ContinuityThreadId,
        payload: serde_json::Value,
    ) -> ContinuityEvent {
        ContinuityEvent {
            thread: thread.clone(),
            event_id: format!("evt-{}", Uuid::new_v4()),
            kind: kind.to_string(),
            payload,
        }
    }
}
