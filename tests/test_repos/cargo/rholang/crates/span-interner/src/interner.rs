use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct InternedString(usize);

pub struct SpanInterner {
    strings: Vec<String>,
    indices: HashMap<String, InternedString>,
}

impl SpanInterner {
    pub fn new() -> Self {
        Self {
            strings: Vec::new(),
            indices: HashMap::new(),
        }
    }

    pub fn intern(&mut self, s: &str) -> InternedString {
        if let Some(&id) = self.indices.get(s) {
            return id;
        }

        let id = InternedString(self.strings.len());
        self.strings.push(s.to_string());
        self.indices.insert(s.to_string(), id);
        id
    }

    pub fn resolve(&self, interned: InternedString) -> Option<&str> {
        self.strings.get(interned.0).map(|s| s.as_str())
    }

    pub fn len(&self) -> usize {
        self.strings.len()
    }

    pub fn is_empty(&self) -> bool {
        self.strings.is_empty()
    }
}

impl Default for SpanInterner {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_interner_basic() {
        let mut interner = SpanInterner::new();
        let id1 = interner.intern("test");
        let id2 = interner.intern("test");
        assert_eq!(id1, id2);
        assert_eq!(interner.resolve(id1), Some("test"));
    }

    #[test]
    fn test_interner_multiple() {
        let mut interner = SpanInterner::new();
        let id1 = interner.intern("foo");
        let id2 = interner.intern("bar");
        assert_ne!(id1, id2);
        assert_eq!(interner.resolve(id1), Some("foo"));
        assert_eq!(interner.resolve(id2), Some("bar"));
    }
}
