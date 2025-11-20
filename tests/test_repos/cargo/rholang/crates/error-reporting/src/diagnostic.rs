//! Diagnostic messages and pretty printing.

/// Diagnostic severity level
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiagnosticLevel {
    Error,
    Warning,
    Info,
    Help,
}

/// A diagnostic message with location and severity
#[derive(Debug, Clone)]
pub struct Diagnostic {
    pub level: DiagnosticLevel,
    pub message: String,
    pub file_id: Option<usize>,
    pub line: Option<usize>,
    pub column: Option<usize>,
}

impl Diagnostic {
    pub fn error(message: impl Into<String>) -> Self {
        Diagnostic {
            level: DiagnosticLevel::Error,
            message: message.into(),
            file_id: None,
            line: None,
            column: None,
        }
    }

    pub fn warning(message: impl Into<String>) -> Self {
        Diagnostic {
            level: DiagnosticLevel::Warning,
            message: message.into(),
            file_id: None,
            line: None,
            column: None,
        }
    }

    pub fn with_location(mut self, file_id: usize, line: usize, column: usize) -> Self {
        self.file_id = Some(file_id);
        self.line = Some(line);
        self.column = Some(column);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_diagnostic_creation() {
        let diag = Diagnostic::error("test error");
        assert_eq!(diag.level, DiagnosticLevel::Error);
        assert_eq!(diag.message, "test error");
    }

    #[test]
    fn test_diagnostic_with_location() {
        let diag = Diagnostic::warning("test warning")
            .with_location(0, 10, 5);
        assert_eq!(diag.file_id, Some(0));
        assert_eq!(diag.line, Some(10));
        assert_eq!(diag.column, Some(5));
    }
}
