use crate::types::*;
use anyhow::Result;
use std::collections::HashMap;
use std::path::PathBuf;

pub trait ContinuityStore: Send + Sync {
    fn create_thread(&self, thread: ContinuityThread) -> Result<()>;
    fn get_thread(&self, id: ThreadId) -> Result<Option<ContinuityThread>>;
    fn list_threads(&self) -> Result<Vec<ContinuityThread>>;

    fn append_event(&self, event: ContinuityEvent) -> Result<()>;
    fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>>;
    fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>>;
}

/// In-memory store for dev / testing.
pub struct InMemoryStore {
    threads: parking_lot::RwLock<HashMap<ThreadId, ContinuityThread>>,
    events: parking_lot::RwLock<HashMap<EventId, ContinuityEvent>>,
}

impl InMemoryStore {
    pub fn new() -> Self {
        Self {
            threads: parking_lot::RwLock::new(HashMap::new()),
            events: parking_lot::RwLock::new(HashMap::new()),
        }
    }
}

impl Default for InMemoryStore {
    fn default() -> Self {
        Self::new()
    }
}

impl ContinuityStore for InMemoryStore {
    fn create_thread(&self, thread: ContinuityThread) -> Result<()> {
        self.threads.write().insert(thread.id, thread);
        Ok(())
    }

    fn get_thread(&self, id: ThreadId) -> Result<Option<ContinuityThread>> {
        Ok(self.threads.read().get(&id).cloned())
    }

    fn list_threads(&self) -> Result<Vec<ContinuityThread>> {
        Ok(self.threads.read().values().cloned().collect())
    }

    fn append_event(&self, event: ContinuityEvent) -> Result<()> {
        self.events.write().insert(event.id, event);
        Ok(())
    }

    fn get_event(&self, id: EventId) -> Result<Option<ContinuityEvent>> {
        Ok(self.events.read().get(&id).cloned())
    }

    fn list_events_for_thread(&self, thread_id: ThreadId) -> Result<Vec<ContinuityEvent>> {
        Ok(self
            .events
            .read()
            .values()
            .filter(|e| e.thread_id == thread_id)
            .cloned()
            .collect())
    }
}

/// Placeholder for a file-backed store (e.g., sled, sqlite, or parquet).
pub struct FileStore {
    pub root: PathBuf,
}

impl FileStore {
    pub fn new(root: PathBuf) -> Self {
        Self { root }
    }
}

// Implement ContinuityStore for FileStore later using your preferred backend.
