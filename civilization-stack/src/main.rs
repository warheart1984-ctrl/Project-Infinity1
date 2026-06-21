use civilization_stack::{
    ContinuityEngine, EventType, InMemoryStore, ReconstructionEngine,
};
use serde_json::json;
use std::sync::Arc;

fn main() -> anyhow::Result<()> {
    let store = Arc::new(InMemoryStore::new());
    let continuity = ContinuityEngine::new(store.clone());
    let recon = ReconstructionEngine::new(continuity.clone());

    let thread = continuity.create_thread(
        Some("NeoMundi Architecture Choice".into()),
        None,
    )?;

    let note = continuity.append_event(
        thread.id,
        EventType::Note,
        json!({"text": "We need a governed world model for NeoMundi."}),
        vec![],
    )?;

    let evidence = continuity.append_event(
        thread.id,
        EventType::Evidence,
        json!({"source": "experiment-2026-06-19", "summary": "Un-governed agents drift."}),
        vec![note.id],
    )?;

    let arch = continuity.append_event(
        thread.id,
        EventType::Architecture,
        json!({"name": "NeoMundi v1", "pattern": "governed world model over FOS"}),
        vec![note.id, evidence.id],
    )?;

    let decision = continuity.append_event(
        thread.id,
        EventType::Decision,
        json!({
            "title": "Adopt NeoMundi v1",
            "rationale": "We need a governed world model integrated with FOS continuity.",
            "chosen_architecture": arch.id,
        }),
        vec![arch.id, evidence.id],
    )?;

    let reconstruction = recon.reconstruct_decision(decision.id)?;

    println!("Decision: {:?}", reconstruction.decision.event_type);
    println!("Discussion events: {}", reconstruction.discussion_events.len());
    println!("Architecture events: {}", reconstruction.architecture_events.len());
    println!("Evidence events: {}", reconstruction.evidence_events.len());
    println!("Outcome events: {}", reconstruction.outcome_events.len());

    Ok(())
}
