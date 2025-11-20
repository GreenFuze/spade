pub mod interner;

pub use interner::{SpanInterner, InternedString};

use common_types::Span;

pub struct SpanManager {
    interner: SpanInterner,
}

impl SpanManager {
    pub fn new() -> Self {
        Self {
            interner: SpanInterner::new(),
        }
    }

    pub fn intern(&mut self, s: &str) -> InternedString {
        self.interner.intern(s)
    }

    pub fn resolve(&self, interned: InternedString) -> Option<&str> {
        self.interner.resolve(interned)
    }
}

impl Default for SpanManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_span_manager() {
        let mut manager = SpanManager::new();
        let id1 = manager.intern("hello");
        let id2 = manager.intern("hello");
        assert_eq!(id1, id2);
    }
}
