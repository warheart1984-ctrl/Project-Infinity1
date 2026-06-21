//! Python FOS continuity.jsonl wire format (shared store authority).

use anyhow::{anyhow, Result};
use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use uuid::Uuid;

use crate::types::{ContinuityEvent, ContinuityThread, EventType, EventId, ThreadId};

pub type WireThreadId = String;
pub type WireEventId = String;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "record_type", rename_all = "snake_case")]
pub enum WireRecord {
    Thread {
        thread_id: WireThreadId,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        parent_thread_id: Option<WireThreadId>,
        #[serde(default)]
        event_ids: Vec<WireEventId>,
    },
    Event {
        event_id: WireEventId,
        thread_id: WireThreadId,
        #[serde(rename = "type")]
        event_type: String,
        #[serde(default)]
        payload: Value,
        timestamp: String,
        #[serde(default)]
        lineage: Vec<WireEventId>,
    },
}

pub fn parse_event_type(raw: &str) -> EventType {
    match raw {
        "Concept" => EventType::Concept,
        "Invariant" => EventType::Invariant,
        "Architecture" => EventType::Architecture,
        "Governance" => EventType::Governance,
        "Decision" => EventType::Decision,
        "Evidence" => EventType::Evidence,
        "Note" => EventType::Note,
        other => EventType::Custom(other.to_string()),
    }
}

pub fn event_type_to_wire(event_type: &EventType) -> String {
    match event_type {
        EventType::Concept => "Concept".to_string(),
        EventType::Invariant => "Invariant".to_string(),
        EventType::Architecture => "Architecture".to_string(),
        EventType::Governance => "Governance".to_string(),
        EventType::Decision => "Decision".to_string(),
        EventType::Evidence => "Evidence".to_string(),
        EventType::Note => "Note".to_string(),
        EventType::Custom(value) => value.clone(),
    }
}

pub fn wire_thread_id_to_uuid(thread_id: &str) -> ThreadId {
    Uuid::parse_str(thread_id).unwrap_or_else(|_| {
        Uuid::new_v5(
            &Uuid::NAMESPACE_URL,
            format!("urn:fos:thread:{thread_id}").as_bytes(),
        )
    })
}

pub fn wire_event_id_to_uuid(event_id: &str) -> EventId {
    Uuid::parse_str(event_id).unwrap_or_else(|_| {
        Uuid::new_v5(
            &Uuid::NAMESPACE_URL,
            format!("urn:fos:event:{event_id}").as_bytes(),
        )
    })
}

pub fn wire_thread_to_native(
    thread_id: &str,
    parent: Option<&str>,
    event_ids: &[String],
) -> ContinuityThread {
    ContinuityThread {
        id: wire_thread_id_to_uuid(thread_id),
        parent: parent.map(wire_thread_id_to_uuid),
        label: Some(thread_id.to_string()),
        created_at: Utc::now(),
    }
}

pub fn native_thread_to_wire(thread: &ContinuityThread) -> WireRecord {
    let thread_id = thread
        .label
        .clone()
        .unwrap_or_else(|| thread.id.to_string());
    WireRecord::Thread {
        thread_id,
        parent_thread_id: thread.parent.map(|id| id.to_string()),
        event_ids: Vec::new(),
    }
}

pub fn wire_event_to_native(
    event_id: &str,
    thread_id: &str,
    event_type: &str,
    payload: Value,
    timestamp: &str,
    lineage: &[String],
) -> Result<ContinuityEvent> {
    let parsed_ts = DateTime::parse_from_rfc3339(timestamp)
        .map(|value| value.with_timezone(&Utc))
        .or_else(|_| {
            timestamp
                .parse::<DateTime<Utc>>()
                .map_err(|error| anyhow!("invalid timestamp: {error}"))
        })?;

    Ok(ContinuityEvent {
        id: wire_event_id_to_uuid(event_id),
        thread_id: wire_thread_id_to_uuid(thread_id),
        event_type: parse_event_type(event_type),
        payload,
        timestamp: parsed_ts,
        lineage: lineage.iter().map(|id| wire_event_id_to_uuid(id)).collect(),
    })
}

pub fn native_event_to_wire(event: &ContinuityEvent) -> WireRecord {
    WireRecord::Event {
        event_id: event.id.to_string(),
        thread_id: event.thread_id.to_string(),
        event_type: event_type_to_wire(&event.event_type),
        payload: event.payload.clone(),
        timestamp: event.timestamp.to_rfc3339(),
        lineage: event.lineage.iter().map(|id| id.to_string()).collect(),
    }
}

pub fn wire_event_to_wire_record(
    event_id: &str,
    thread_id: &str,
    event_type: &str,
    payload: Value,
    timestamp: &str,
    lineage: &[String],
) -> WireRecord {
    WireRecord::Event {
        event_id: event_id.to_string(),
        thread_id: thread_id.to_string(),
        event_type: event_type.to_string(),
        payload,
        timestamp: timestamp.to_string(),
        lineage: lineage.iter().cloned().collect(),
    }
}
