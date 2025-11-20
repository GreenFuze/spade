//! Error reporting and diagnostic utilities for the RhoLang compiler.

pub mod diagnostic;

pub use diagnostic::{Diagnostic, DiagnosticLevel};

use thiserror::Error;

/// Core compiler error types
#[derive(Error, Debug)]
pub enum CompilerError {
    #[error("Syntax error: {0}")]
    Syntax(String),

    #[error("Type error: {0}")]
    Type(String),

    #[error("Name error: {0}")]
    Name(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compiler_error_creation() {
        let err = CompilerError::Syntax("unexpected token".to_string());
        assert!(err.to_string().contains("Syntax error"));
    }
}
