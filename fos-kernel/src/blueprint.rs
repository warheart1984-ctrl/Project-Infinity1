use serde::{Deserialize, Serialize};
use uuid::Uuid;

use crate::types::{ContinuityThreadId, Id, MemoryObject, MemoryType, Version};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "PascalCase")]
pub enum BlueprintKind {
    Architecture,
    Governance,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Blueprint {
    pub id: Id,
    pub source_ids: Vec<Id>,
    pub kind: BlueprintKind,
    pub content: serde_json::Value,
    pub version: Version,
    pub continuity_thread: ContinuityThreadId,
}

pub struct BlueprintCompiler;

impl BlueprintCompiler {
    pub fn from_memory(
        continuity_thread: ContinuityThreadId,
        sources: &[MemoryObject],
        kind: BlueprintKind,
    ) -> Blueprint {
        let source_ids: Vec<Id> = sources.iter().map(|o| o.id.clone()).collect();
        let content = serde_json::json!({
            "sources": source_ids,
            "kind": format!("{:?}", kind),
        });
        Blueprint {
            id: format!("bp-{}", Uuid::new_v4()),
            source_ids,
            kind,
            content,
            version: Version::from("v0.1.0"),
            continuity_thread,
        }
    }

    pub fn select_architecture_sources<'a>(
        objs: impl Iterator<Item = &'a MemoryObject>,
    ) -> Vec<&'a MemoryObject> {
        objs.filter(|o| {
            matches!(
                o.mtype,
                MemoryType::Architecture | MemoryType::SystemModel
            )
        })
        .collect()
    }

    pub fn select_governance_sources<'a>(
        objs: impl Iterator<Item = &'a MemoryObject>,
    ) -> Vec<&'a MemoryObject> {
        objs.filter(|o| {
            matches!(
                o.mtype,
                MemoryType::GovernanceContract | MemoryType::Invariant
            )
        })
        .collect()
    }
}
