use crate::storage::ContinuityStore;
use crate::types::*;
use anyhow::{anyhow, Result};
use chrono::Utc;
use std::collections::HashSet;
use std::sync::Arc;
use uuid::Uuid;

#[derive(Clone)]
pub struct ContinuityEngine<S: ContinuityStore + 'static> {
    store: Arc<S>,
}

impl<S: ContinuityStore> ContinuityEngine<S> {
    pub fn new(store: Arc<S>) -> Self {
        Self { store }
    }

    pub fn store(&self) -> &Arc<S> {
        &self.store
    }

    // --- Threads ---

    pub fn create_thread(
        &self,
        label: Option<String>,
        parent: Option<ThreadId>,
    ) -> Result<ContinuityThread> {
        let thread = ContinuityThread {
            id: Uuid::new_v4(),
            parent,
            label,
            created_at: Utc::now(),
        };
        self.store.create_thread(thread.clone())?;
        Ok(thread)
    }

    pub fn get_thread(&self, id: ThreadId) -> Result<Option<ContinuityThread>> {
        self.store.get_thread(id)
    }

    pub fn list_threads(&self) -> Result<Vec<ContinuityThread>> {
        self.store.list_threads()
    }

    // --- Events ---

    pub fn append_event(
        &self,
        thread_id: ThreadId,
        event_type: EventType,
        payload: serde_json::Value,
        lineage: Vec<EventId>,
    ) -> Result<ContinuityEvent> {
        if self.store.get_thread(thread_id)?.is_none() {
            return Err(anyhow!("Thread does not exist"));
        }

        let event = ContinuityEvent {
            id: Uuid::new_v4(),
            thread_id,
            event_type,
            payload,
            timestamp: Utc::now(),
            lineage,
        };

        self.store.append_event(event.clone())?;
        Ok(event)
    }

    pub fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>> {
        self.store.get_event(id)
    }

    pub fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>> {
        let mut events = self.store.list_events_for_thread(thread_id)?;
        events.sort_by_key(|e| e.timestamp);
        Ok(events)
    }

    // --- Lineage traversal ---

    pub fn get_lineage_chain(&self, start: EventId) -> Result<Vec<ContinuityEvent>> {
        let mut result = Vec::new();
        let mut stack = vec![start];
        let mut seen = HashSet::new();

        while let Some(current_id) = stack.pop() {
            if !seen.insert(current_id) {
                continue;
            }
            if let Some(ev) = self.store.get_event(current_id)? {
                for parent in &ev.lineage {
                    stack.push(*parent);
                }
                result.push(ev);
            }
        }

        Ok(result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::storage::InMemoryStore;
    use serde_json::json;

    #[test]
    fn create_thread_and_append_event() {
        let store = Arc::new(InMemoryStore::new());
        let engine = ContinuityEngine::new(store);

        let thread = engine
            .create_thread(Some("test-thread".into()), None)
            .unwrap();
        let event = engine
            .append_event(
                thread.id,
                EventType::Note,
                json!({"text": "hello"}),
                vec![],
            )
            .unwrap();

        assert_eq!(event.thread_id, thread.id);
        assert_eq!(engine.list_events_for_thread(thread.id).unwrap().len(), 1);
    }

    #[test]
    fn lineage_chain_follows_pointers() {
        let store = Arc::new(InMemoryStore::new());
        let engine = ContinuityEngine::new(store);
        let thread = engine.create_thread(None, None).unwrap();

        let root = engine
            .append_event(thread.id, EventType::Concept, json!({}), vec![])
            .unwrap();
        let child = engine
            .append_event(
                thread.id,
                EventType::Evidence,
                json!({}),
                vec![root.id],
            )
            .unwrap();

        let chain = engine.get_lineage_chain(child.id).unwrap();
        assert_eq!(chain.len(), 2);
    }
}
