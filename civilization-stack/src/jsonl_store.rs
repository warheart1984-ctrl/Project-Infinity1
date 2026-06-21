//! Append-only JSONL store — wire-compatible with Python `ContinuityEngine`.

use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use chrono::Utc;
use parking_lot::RwLock;
use serde_json::Value;
use uuid::Uuid;

use crate::interop::{WireEventId, WireRecord, WireThreadId};
use crate::types::{ContinuityEvent, ContinuityThread, EventType};

#[derive(Debug, Clone)]
pub struct JsonlStore {
    path: PathBuf,
    threads: RwLock<std::collections::HashMap<WireThreadId, ContinuityThreadWire>>,
    events: RwLock<std::collections::HashMap<WireEventId, ContinuityEventWire>>,
}

#[derive(Debug, Clone)]
pub struct ContinuityThreadWire {
    thread_id: WireThreadId,
    parent_thread_id: Option<WireThreadId>,
    event_ids: Vec<WireEventId>,
}

#[derive(Debug, Clone)]
pub struct ContinuityEventWire {
    pub event_id: WireEventId,
    pub thread_id: WireThreadId,
    pub event_type: String,
    pub payload: Value,
    pub timestamp: String,
    pub lineage: Vec<WireEventId>,
}

impl JsonlStore {
    pub fn new(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref().to_path_buf();
        let store = Self {
            path,
            threads: RwLock::new(std::collections::HashMap::new()),
            events: RwLock::new(std::collections::HashMap::new()),
        };
        if store.path.exists() {
            store.reload()?;
        }
        Ok(store)
    }

    pub fn path(&self) -> &Path {
        &self.path
    }

    pub fn reload(&self) -> Result<()> {
        self.threads.write().clear();
        self.events.write().clear();
        if !self.path.exists() {
            return Ok(());
        }
        let file = File::open(&self.path).with_context(|| format!("open {}", self.path.display()))?;
        for line in BufReader::new(file).lines() {
            let line = line?;
            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }
            let record: WireRecord = serde_json::from_str(trimmed)?;
            match record {
                WireRecord::Thread {
                    thread_id,
                    parent_thread_id,
                    event_ids,
                } => {
                    self.threads.write().insert(
                        thread_id.clone(),
                        ContinuityThreadWire {
                            thread_id,
                            parent_thread_id,
                            event_ids,
                        },
                    );
                }
                WireRecord::Event {
                    event_id,
                    thread_id,
                    event_type,
                    payload,
                    timestamp,
                    lineage,
                } => {
                    {
                        let mut threads = self.threads.write();
                        let entry = threads.entry(thread_id.clone()).or_insert_with(|| {
                            ContinuityThreadWire {
                                thread_id: thread_id.clone(),
                                parent_thread_id: None,
                                event_ids: Vec::new(),
                            }
                        });
                        if !entry.event_ids.contains(&event_id) {
                            entry.event_ids.push(event_id.clone());
                        }
                    }
                    self.events.write().insert(
                        event_id.clone(),
                        ContinuityEventWire {
                            event_id,
                            thread_id,
                            event_type,
                            payload,
                            timestamp,
                            lineage,
                        },
                    );
                }
            }
        }
        Ok(())
    }

    fn append_record(&self, record: &WireRecord) -> Result<()> {
        if let Some(parent) = self.path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(&self.path)?;
        let line = serde_json::to_string(record)?;
        writeln!(file, "{line}")?;
        Ok(())
    }

    pub fn ensure_thread(&self, thread_id: &str, parent: Option<&str>) -> Result<()> {
        if self.threads.read().contains_key(thread_id) {
            return Ok(());
        }
        let record = WireRecord::Thread {
            thread_id: thread_id.to_string(),
            parent_thread_id: parent.map(str::to_string),
            event_ids: Vec::new(),
        };
        self.append_record(&record)?;
        self.threads.write().insert(
            thread_id.to_string(),
            ContinuityThreadWire {
                thread_id: thread_id.to_string(),
                parent_thread_id: parent.map(str::to_string),
                event_ids: Vec::new(),
            },
        );
        Ok(())
    }

    pub fn append_event(
        &self,
        thread_id: &str,
        event_type: EventType,
        payload: Value,
        lineage: Vec<String>,
        event_id: Option<String>,
    ) -> Result<ContinuityEventWire> {
        self.ensure_thread(thread_id, None)?;
        let event_id = event_id.unwrap_or_else(|| format!("evt-{}", Uuid::new_v4()));
        if self.events.read().contains_key(&event_id) {
            anyhow::bail!("event already exists: {event_id}");
        }
        let timestamp = Utc::now().format("%Y-%m-%dT%H:%M:%SZ").to_string();
        let event_type_str = crate::interop::event_type_to_wire(&event_type);
        let record = WireRecord::Event {
            event_id: event_id.clone(),
            thread_id: thread_id.to_string(),
            event_type: event_type_str.clone(),
            payload: payload.clone(),
            timestamp: timestamp.clone(),
            lineage: lineage.clone(),
        };
        self.append_record(&record)?;
        {
            let mut threads = self.threads.write();
            if let Some(thread) = threads.get_mut(thread_id) {
                thread.event_ids.push(event_id.clone());
            }
        }
        let wire = ContinuityEventWire {
            event_id,
            thread_id: thread_id.to_string(),
            event_type: event_type_str,
            payload,
            timestamp,
            lineage,
        };
        self.events.write().insert(wire.event_id.clone(), wire.clone());
        Ok(wire)
    }

    pub fn get_event(&self, event_id: &str) -> Option<ContinuityEventWire> {
        self.events.read().get(event_id).cloned()
    }

    pub fn list_events_for_thread(&self, thread_id: &str) -> Vec<ContinuityEventWire> {
        let thread = self.threads.read().get(thread_id).cloned();
        let Some(thread) = thread else {
            return Vec::new();
        };
        let events = self.events.read();
        thread
            .event_ids
            .iter()
            .filter_map(|id| events.get(id).cloned())
            .collect()
    }

    pub fn list_threads(&self) -> Vec<ContinuityThreadWire> {
        self.threads.read().values().cloned().collect()
    }
}

impl ContinuityThreadWire {
    pub fn to_native(&self) -> ContinuityThread {
        crate::interop::wire_thread_to_native(
            &self.thread_id,
            self.parent_thread_id.as_deref(),
            &self.event_ids,
        )
    }
}

impl ContinuityEventWire {
    pub fn to_native(&self) -> Result<ContinuityEvent> {
        crate::interop::wire_event_to_native(
            &self.event_id,
            &self.thread_id,
            &self.event_type,
            self.payload.clone(),
            &self.timestamp,
            &self.lineage,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn round_trip_jsonl_records() {
        let dir = std::env::temp_dir().join(format!("fos-jsonl-{}", Uuid::new_v4()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("continuity.jsonl");
        let store = JsonlStore::new(&path).unwrap();
        store.ensure_thread("dar-z", None).unwrap();
        let event = store
            .append_event(
                "dar-z",
                EventType::Evidence,
                json!({"source": "darz-kernel"}),
                vec![],
                Some("evt-test-001".into()),
            )
            .unwrap();
        drop(store);

        let reloaded = JsonlStore::new(&path).unwrap();
        assert_eq!(reloaded.get_event(&event.event_id).unwrap().thread_id, "dar-z");
    }
}
