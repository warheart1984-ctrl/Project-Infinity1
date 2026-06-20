use serde::{Deserialize, Serialize};

use crate::types::{ContinuityThreadId, EvidenceRef, Id, MemoryObject, MemoryType, Version};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RawConversation {
    pub id: Id,
    pub text: String,
    pub continuity_thread: ContinuityThreadId,
}

pub struct TranslationEngine;

impl TranslationEngine {
    pub fn conversation_to_memory(conv: &RawConversation) -> Vec<MemoryObject> {
        conv.text
            .split("\n\n")
            .enumerate()
            .filter(|(_, chunk)| !chunk.trim().is_empty())
            .map(|(i, chunk)| MemoryObject {
                id: format!("mem-{}-{}", conv.id, i),
                mtype: MemoryType::Concept,
                definition: chunk.trim().to_string(),
                evidence_refs: Vec::<EvidenceRef>::new(),
                lineage: vec![conv.id.clone()],
                version: Version::from("v0.1.0"),
                continuity_thread: conv.continuity_thread.clone(),
            })
            .collect()
    }
}
