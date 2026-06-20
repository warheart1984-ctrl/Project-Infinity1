use crate::blueprint::{BlueprintCompiler, BlueprintKind};
use crate::continuity::ContinuityEngine;
use crate::memory_core::MemoryCore;
use crate::translation::{RawConversation, TranslationEngine};
use crate::validation::ValidationLayer;

pub struct FosKernel {
    pub memory: MemoryCore,
}

impl FosKernel {
    pub fn new() -> Self {
        Self {
            memory: MemoryCore::new(),
        }
    }

    pub fn ingest_conversation(&mut self, conv: &RawConversation) {
        let objs = TranslationEngine::conversation_to_memory(conv);
        for obj in objs {
            if ValidationLayer::validate_memory(&obj) {
                self.memory.upsert(obj);
            }
        }
    }

    pub fn compile_architecture_blueprint(&self, thread: &str) -> serde_json::Value {
        let sources = BlueprintCompiler::select_architecture_sources(self.memory.all());
        let bp = BlueprintCompiler::from_memory(
            thread.to_string(),
            &sources,
            BlueprintKind::Architecture,
        );
        let evt = ContinuityEngine::emit(
            "blueprint:architecture",
            &bp.continuity_thread,
            serde_json::to_value(&bp).unwrap(),
        );
        serde_json::to_value(evt).unwrap()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ingest_and_compile() {
        let mut kernel = FosKernel::new();
        kernel.ingest_conversation(&RawConversation {
            id: "conv-1".into(),
            text: "Founder memory".into(),
            continuity_thread: "thread-1".into(),
        });
        let event = kernel.compile_architecture_blueprint("thread-1");
        assert_eq!(event["kind"], "blueprint:architecture");
    }
}
