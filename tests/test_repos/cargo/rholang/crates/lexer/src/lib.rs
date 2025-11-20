pub mod token;
pub mod scanner;

pub use token::{Token, TokenKind};
pub use scanner::Scanner;

use common_types::Span;
use error_reporting::Diagnostic;

pub struct Lexer {
    scanner: Scanner,
}

impl Lexer {
    pub fn new(input: &str) -> Self {
        Self {
            scanner: Scanner::new(input),
        }
    }

    pub fn tokenize(&mut self) -> Result<Vec<Token>, Diagnostic> {
        self.scanner.scan_tokens()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lexer_basic() {
        let mut lexer = Lexer::new("let x = 42");
        let result = lexer.tokenize();
        assert!(result.is_ok());
    }
}
