//! Typed projections over raw ContinuityEvent payloads.

use anyhow::{anyhow, Result};
use serde_json::Value;
use uuid::Uuid;

use crate::model::{ArchitectureBlueprint, Concept, Decision, GovernanceContract};
use crate::types::{ContinuityEvent, EventId, EventType, ThreadId};

fn event_id(value: &ContinuityEvent) -> EventId {
    value.id
}

fn thread_id(value: &ContinuityEvent) -> ThreadId {
    value.thread_id
}

fn string_field(payload: &Value, key: &str) -> Result<String> {
    payload
        .get(key)
        .and_then(Value::as_str)
        .map(str::to_string)
        .ok_or_else(|| anyhow!("missing or invalid field: {key}"))
}

fn optional_string(payload: &Value, key: &str) -> Option<String> {
    payload.get(key).and_then(Value::as_str).map(str::to_string)
}

fn string_list(payload: &Value, key: &str) -> Vec<String> {
    payload
        .get(key)
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .map(str::to_string)
                .collect()
        })
        .unwrap_or_default()
}

fn event_id_list(payload: &Value, key: &str) -> Vec<EventId> {
    payload
        .get(key)
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(|item| {
                    item.as_str()
                        .map(str::to_string)
                        .or_else(|| item.as_str().map(str::to_string))
                        .and_then(|raw| Uuid::parse_str(&raw).ok())
                })
                .collect()
        })
        .unwrap_or_default()
}

pub fn project_concept(event: &ContinuityEvent) -> Result<Concept> {
    if event.event_type != EventType::Concept {
        return Err(anyhow!("event is not Concept"));
    }
    Ok(Concept {
        id: event_id(event),
        thread_id: thread_id(event),
        name: string_field(&event.payload, "name").or_else(|_| {
            string_field(&event.payload, "title")
        })?,
        definition: string_field(&event.payload, "definition").or_else(|_| {
            optional_string(&event.payload, "text")
                .ok_or_else(|| anyhow!("missing definition"))
        })?,
        evidence_refs: event_id_list(&event.payload, "evidence_refs"),
        lineage: event.lineage.clone(),
    })
}

pub fn project_architecture(event: &ContinuityEvent) -> Result<ArchitectureBlueprint> {
    if event.event_type != EventType::Architecture {
        return Err(anyhow!("event is not Architecture"));
    }
    Ok(ArchitectureBlueprint {
        id: event_id(event),
        thread_id: thread_id(event),
        name: string_field(&event.payload, "name")?,
        version: optional_string(&event.payload, "version").unwrap_or_else(|| "v0.1".to_string()),
        definition: string_field(&event.payload, "definition").or_else(|_| {
            optional_string(&event.payload, "pattern")
                .ok_or_else(|| anyhow!("missing definition"))
        })?,
        invariants: string_list(&event.payload, "invariants"),
        components: string_list(&event.payload, "components"),
        evidence_refs: event_id_list(&event.payload, "evidence_refs"),
        lineage: event.lineage.clone(),
    })
}

pub fn project_governance(event: &ContinuityEvent) -> Result<GovernanceContract> {
    if event.event_type != EventType::Governance {
        return Err(anyhow!("event is not Governance"));
    }
    Ok(GovernanceContract {
        id: event_id(event),
        thread_id: thread_id(event),
        name: string_field(&event.payload, "name")?,
        authority_scope: string_field(&event.payload, "authority_scope")
            .or_else(|_| string_field(&event.payload, "scope"))?,
        invariants: string_list(&event.payload, "invariants"),
        constraints: string_list(&event.payload, "constraints"),
        evidence_refs: event_id_list(&event.payload, "evidence_refs"),
        lineage: event.lineage.clone(),
    })
}

pub fn project_decision(event: &ContinuityEvent) -> Result<Decision> {
    if event.event_type != EventType::Decision {
        return Err(anyhow!("event is not Decision"));
    }
    let chosen = event
        .payload
        .get("chosen_architecture")
        .and_then(|value| {
            value
                .as_str()
                .and_then(|raw| Uuid::parse_str(raw).ok())
                .or_else(|| {
                    value
                        .as_str()
                        .map(str::to_string)
                        .and_then(|raw| Uuid::parse_str(&raw).ok())
                })
        });
    Ok(Decision {
        id: event_id(event),
        thread_id: thread_id(event),
        title: string_field(&event.payload, "title")?,
        rationale: string_field(&event.payload, "rationale").unwrap_or_default(),
        chosen_architecture: chosen,
        alternatives: event_id_list(&event.payload, "alternatives"),
        evidence_refs: event_id_list(&event.payload, "evidence_refs"),
        governance_refs: event_id_list(&event.payload, "governance_refs"),
        outcome_summary: optional_string(&event.payload, "outcome_summary"),
        lineage: event.lineage.clone(),
    })
}

pub fn project_event(event: &ContinuityEvent) -> Result<ProjectedEvent> {
    match event.event_type {
        EventType::Concept => Ok(ProjectedEvent::Concept(project_concept(event)?)),
        EventType::Architecture => Ok(ProjectedEvent::Architecture(project_architecture(event)?)),
        EventType::Governance => Ok(ProjectedEvent::Governance(project_governance(event)?)),
        EventType::Decision => Ok(ProjectedEvent::Decision(project_decision(event)?)),
        _ => Err(anyhow!("no typed projection for {:?}", event.event_type)),
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ProjectedEvent {
    Concept(Concept),
    Architecture(ArchitectureBlueprint),
    Governance(GovernanceContract),
    Decision(Decision),
}
