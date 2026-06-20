use crate::types::MemoryObject;

pub struct ValidationLayer;

impl ValidationLayer {
    pub fn validate_memory(obj: &MemoryObject) -> bool {
        !obj.definition.trim().is_empty()
            && !obj.version.is_empty()
            && !obj.continuity_thread.is_empty()
    }
}
