use std::collections::HashMap;

use crate::types::{Id, MemoryObject};

#[derive(Default)]
pub struct MemoryCore {
    objects: HashMap<Id, MemoryObject>,
}

impl MemoryCore {
    pub fn new() -> Self {
        Self {
            objects: HashMap::new(),
        }
    }

    pub fn upsert(&mut self, obj: MemoryObject) {
        self.objects.insert(obj.id.clone(), obj);
    }

    pub fn get(&self, id: &Id) -> Option<&MemoryObject> {
        self.objects.get(id)
    }

    pub fn all(&self) -> impl Iterator<Item = &MemoryObject> {
        self.objects.values()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::types::{MemoryType, Version};

    #[test]
    fn upsert_and_get() {
        let mut core = MemoryCore::new();
        let obj = MemoryObject {
            id: "mem-1".into(),
            mtype: MemoryType::Concept,
            definition: "test".into(),
            evidence_refs: vec![],
            lineage: vec!["conv-1".into()],
            version: Version::from("v0.1.0"),
            continuity_thread: "thread-1".into(),
        };
        core.upsert(obj);
        assert!(core.get(&"mem-1".into()).is_some());
    }
}
