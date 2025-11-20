pub mod expr;
pub mod stmt;
pub mod decl;

pub use expr::{Expr, ExprKind};
pub use stmt::{Stmt, StmtKind};
pub use decl::{Decl, DeclKind};

use lexer::{Token, TokenKind};
use common_types::Span;
use error_reporting::Diagnostic;

pub struct Parser {
    tokens: Vec<Token>,
    current: usize,
}

impl Parser {
    pub fn new(tokens: Vec<Token>) -> Self {
        Self { tokens, current: 0 }
    }

    pub fn parse(&mut self) -> Result<Vec<Decl>, Diagnostic> {
        let mut declarations = Vec::new();

        while !self.is_at_end() {
            if let Some(decl) = self.declaration()? {
                declarations.push(decl);
            }
        }

        Ok(declarations)
    }

    fn declaration(&mut self) -> Result<Option<Decl>, Diagnostic> {
        if self.match_token(&[TokenKind::Let]) {
            Ok(Some(self.let_declaration()?))
        } else if self.match_token(&[TokenKind::Fn]) {
            Ok(Some(self.fn_declaration()?))
        } else {
            self.advance();
            Ok(None)
        }
    }

    fn let_declaration(&mut self) -> Result<Decl, Diagnostic> {
        let span = self.previous().span;
        Ok(Decl {
            kind: DeclKind::Let {
                name: "placeholder".to_string(),
            },
            span,
        })
    }

    fn fn_declaration(&mut self) -> Result<Decl, Diagnostic> {
        let span = self.previous().span;
        Ok(Decl {
            kind: DeclKind::Function {
                name: "placeholder".to_string(),
            },
            span,
        })
    }

    fn match_token(&mut self, kinds: &[TokenKind]) -> bool {
        for kind in kinds {
            if self.check(kind) {
                self.advance();
                return true;
            }
        }
        false
    }

    fn check(&self, kind: &TokenKind) -> bool {
        if self.is_at_end() {
            return false;
        }
        std::mem::discriminant(&self.peek().kind) == std::mem::discriminant(kind)
    }

    fn advance(&mut self) -> &Token {
        if !self.is_at_end() {
            self.current += 1;
        }
        self.previous()
    }

    fn is_at_end(&self) -> bool {
        matches!(self.peek().kind, TokenKind::Eof)
    }

    fn peek(&self) -> &Token {
        &self.tokens[self.current]
    }

    fn previous(&self) -> &Token {
        &self.tokens[self.current - 1]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parser_empty() {
        let tokens = vec![Token::new(TokenKind::Eof, Span::new(0, 0), String::new())];
        let mut parser = Parser::new(tokens);
        let result = parser.parse();
        assert!(result.is_ok());
    }
}
