//! Source span and location tracking.

use serde::{Deserialize, Serialize};

/// Represents a location in source code (file, line, column)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct SourceLocation {
    pub file_id: super::FileId,
    pub line: usize,
    pub column: usize,
}

impl SourceLocation {
    pub fn new(file_id: super::FileId, line: usize, column: usize) -> Self {
        SourceLocation { file_id, line, column }
    }
}

/// Represents a span of source code (start and end positions)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Span {
    pub start: usize,
    pub end: usize,
    pub file_id: super::FileId,
}

impl Span {
    pub fn new(start: usize, end: usize, file_id: super::FileId) -> Self {
        Span { start, end, file_id }
    }

    pub fn len(&self) -> usize {
        self.end.saturating_sub(self.start)
    }

    pub fn is_empty(&self) -> bool {
        self.start >= self.end
    }

    pub fn merge(&self, other: &Span) -> Span {
        assert_eq!(self.file_id, other.file_id, "Cannot merge spans from different files");
        Span {
            start: self.start.min(other.start),
            end: self.end.max(other.end),
            file_id: self.file_id,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::FileId;

    #[test]
    fn test_span_creation() {
        let file_id = FileId::new(0);
        let span = Span::new(10, 20, file_id);
        assert_eq!(span.start, 10);
        assert_eq!(span.end, 20);
        assert_eq!(span.len(), 10);
    }

    #[test]
    fn test_span_merge() {
        let file_id = FileId::new(0);
        let span1 = Span::new(10, 20, file_id);
        let span2 = Span::new(15, 30, file_id);
        let merged = span1.merge(&span2);
        assert_eq!(merged.start, 10);
        assert_eq!(merged.end, 30);
    }

    #[test]
    fn test_source_location() {
        let file_id = FileId::new(0);
        let loc = SourceLocation::new(file_id, 42, 10);
        assert_eq!(loc.line, 42);
        assert_eq!(loc.column, 10);
    }
}
