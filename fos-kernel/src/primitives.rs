use serde::{Deserialize, Serialize};

pub type Id = String;
pub type ThreadId = String;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "PascalCase")]
pub enum EventType {
    Concept,
    Architecture,
    Governance,
    Decision,
    Evidence,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContinuityThread {
    pub thread_id: ThreadId,
    pub parent_thread_id: Option<ThreadId>,
    pub event_ids: Vec<Id>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ContinuityEvent {
    pub event_id: Id,
    pub thread_id: ThreadId,
    #[serde(rename = "type")]
    pub event_type: String,
    pub payload: serde_json::Value,
    pub timestamp: String,
    pub lineage: Vec<Id>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct LineagePointer {
    pub from_event_id: Id,
    pub to_event_id: Id,
}

impl LineagePointer {
    pub fn from_lineage(event_id: &Id, lineage: &[Id]) -> Vec<LineagePointer> {
        lineage
            .iter()
            .map(|parent| LineagePointer {
                from_event_id: event_id.clone(),
                to_event_id: parent.clone(),
            })
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn lineage_pointers_direct() {
        let pointers = LineagePointer::from_lineage(
            &"evt-3".into(),
            &["evt-2".into(), "evt-1".into()],
        );
        assert_eq!(pointers.len(), 2);
        assert_eq!(pointers[0].from_event_id, "evt-3");
        assert_eq!(pointers[0].to_event_id, "evt-2");
        assert_eq!(pointers[1].to_event_id, "evt-1");
    }
}
