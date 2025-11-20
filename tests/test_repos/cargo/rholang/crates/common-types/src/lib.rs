//! Common types and utilities for the RhoLang compiler.
//!
//! This crate provides shared data structures used across all compiler stages.

pub mod span;
pub mod symbol;

pub use span::{Span, SourceLocation};
pub use symbol::{Symbol, SymbolTable};

/// A unique identifier for source file tracking
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct FileId(pub usize);

impl FileId {
    pub fn new(id: usize) -> Self {
        FileId(id)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_file_id_creation() {
        let file_id = FileId::new(42);
        assert_eq!(file_id.0, 42);
    }

    #[test]
    fn test_file_id_equality() {
        let file_id1 = FileId::new(1);
        let file_id2 = FileId::new(1);
        let file_id3 = FileId::new(2);
        assert_eq!(file_id1, file_id2);
        assert_ne!(file_id1, file_id3);
    }
}
