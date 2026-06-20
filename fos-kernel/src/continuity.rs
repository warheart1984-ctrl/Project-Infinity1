use std::collections::HashMap;

use uuid::Uuid;

use crate::primitives::{ContinuityEvent, ContinuityThread, Id, LineagePointer, ThreadId};

pub struct ContinuityEngine {
    threads: HashMap<ThreadId, ContinuityThread>,
    events: HashMap<Id, ContinuityEvent>,
}

impl ContinuityEngine {
    pub fn new() -> Self {
        Self {
            threads: HashMap::new(),
            events: HashMap::new(),
        }
    }

    pub fn create_thread(
        &mut self,
        thread_id: ThreadId,
        parent_thread_id: Option<ThreadId>,
    ) -> ContinuityThread {
        if let Some(existing) = self.threads.get(&thread_id) {
            return existing.clone();
        }
        let thread = ContinuityThread {
            thread_id: thread_id.clone(),
            parent_thread_id,
            event_ids: Vec::new(),
        };
        self.threads.insert(thread_id, thread.clone());
        thread
    }

    pub fn append_event(
        &mut self,
        thread_id: ThreadId,
        event_type: String,
        payload: serde_json::Value,
        lineage: Vec<Id>,
        event_id: Option<Id>,
    ) -> ContinuityEvent {
        self.create_thread(thread_id.clone(), None);
        let resolved_id = event_id.unwrap_or_else(|| format!("evt-{}", Uuid::new_v4()));
        let event = ContinuityEvent {
            event_id: resolved_id.clone(),
            thread_id: thread_id.clone(),
            event_type,
            payload,
            timestamp: "v0.1.0".into(),
            lineage,
        };
        self.events.insert(resolved_id.clone(), event.clone());
        if let Some(thread) = self.threads.get_mut(&thread_id) {
            thread.event_ids.push(resolved_id);
        }
        event
    }

    pub fn query_thread(&self, thread_id: &ThreadId) -> Vec<ContinuityEvent> {
        self.threads
            .get(thread_id)
            .map(|thread| {
                thread
                    .event_ids
                    .iter()
                    .filter_map(|id| self.events.get(id).cloned())
                    .collect()
            })
            .unwrap_or_default()
    }

    pub fn lineage_pointers(&self, event_id: &Id) -> Vec<LineagePointer> {
        self.events
            .get(event_id)
            .map(|event| LineagePointer::from_lineage(event_id, &event.lineage))
            .unwrap_or_default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::primitives::EventType;

    #[test]
    fn append_and_query_thread() {
        let mut engine = ContinuityEngine::new();
        engine.create_thread("thread-1".into(), None);
        engine.append_event(
            "thread-1".into(),
            format!("{:?}", EventType::Concept),
            serde_json::json!({"definition": "test"}),
            vec![],
            None,
        );
        assert_eq!(engine.query_thread(&"thread-1".into()).len(), 1);
    }
}
