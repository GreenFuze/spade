use crate::token::{Token, TokenKind};
use common_types::Span;
use error_reporting::Diagnostic;

pub struct Scanner {
    source: String,
    tokens: Vec<Token>,
    start: usize,
    current: usize,
    line: usize,
}

impl Scanner {
    pub fn new(source: &str) -> Self {
        Self {
            source: source.to_string(),
            tokens: Vec::new(),
            start: 0,
            current: 0,
            line: 1,
        }
    }

    pub fn scan_tokens(&mut self) -> Result<Vec<Token>, Diagnostic> {
        while !self.is_at_end() {
            self.start = self.current;
            self.scan_token()?;
        }

        self.tokens.push(Token::new(
            TokenKind::Eof,
            Span::new(self.current, self.current),
            String::new(),
        ));

        Ok(self.tokens.clone())
    }

    fn scan_token(&mut self) -> Result<(), Diagnostic> {
        let c = self.advance();

        match c {
            ' ' | '\r' | '\t' => {
                // Skip whitespace
            }
            '\n' => {
                self.line += 1;
            }
            '(' => self.add_token(TokenKind::LeftParen),
            ')' => self.add_token(TokenKind::RightParen),
            '{' => self.add_token(TokenKind::LeftBrace),
            '}' => self.add_token(TokenKind::RightBrace),
            '[' => self.add_token(TokenKind::LeftBracket),
            ']' => self.add_token(TokenKind::RightBracket),
            ',' => self.add_token(TokenKind::Comma),
            ';' => self.add_token(TokenKind::Semicolon),
            ':' => self.add_token(TokenKind::Colon),
            '+' => self.add_token(TokenKind::Plus),
            '-' => {
                if self.match_char('>') {
                    self.add_token(TokenKind::Arrow);
                } else {
                    self.add_token(TokenKind::Minus);
                }
            }
            '*' => self.add_token(TokenKind::Star),
            '/' => self.add_token(TokenKind::Slash),
            '=' => {
                if self.match_char('=') {
                    self.add_token(TokenKind::EqualEqual);
                } else {
                    self.add_token(TokenKind::Equal);
                }
            }
            '!' => {
                if self.match_char('=') {
                    self.add_token(TokenKind::BangEqual);
                } else {
                    self.add_token(TokenKind::Bang);
                }
            }
            '<' => {
                if self.match_char('=') {
                    self.add_token(TokenKind::LessEqual);
                } else {
                    self.add_token(TokenKind::Less);
                }
            }
            '>' => {
                if self.match_char('=') {
                    self.add_token(TokenKind::GreaterEqual);
                } else {
                    self.add_token(TokenKind::Greater);
                }
            }
            '"' => self.string()?,
            c if c.is_ascii_digit() => self.number(),
            c if c.is_alphabetic() || c == '_' => self.identifier(),
            _ => {}
        }

        Ok(())
    }

    fn identifier(&mut self) {
        while self.peek().is_alphanumeric() || self.peek() == '_' {
            self.advance();
        }

        let text = &self.source[self.start..self.current];
        let kind = Token::keyword(text).unwrap_or_else(|| TokenKind::Identifier(text.to_string()));
        self.add_token(kind);
    }

    fn number(&mut self) {
        while self.peek().is_ascii_digit() {
            self.advance();
        }

        let text = &self.source[self.start..self.current];
        let value = text.parse::<i64>().unwrap_or(0);
        self.add_token(TokenKind::Number(value));
    }

    fn string(&mut self) -> Result<(), Diagnostic> {
        while self.peek() != '"' && !self.is_at_end() {
            if self.peek() == '\n' {
                self.line += 1;
            }
            self.advance();
        }

        if self.is_at_end() {
            return Ok(());
        }

        self.advance(); // Closing "

        let value = &self.source[self.start + 1..self.current - 1];
        self.add_token(TokenKind::String(value.to_string()));
        Ok(())
    }

    fn match_char(&mut self, expected: char) -> bool {
        if self.is_at_end() {
            return false;
        }
        if self.source.chars().nth(self.current) != Some(expected) {
            return false;
        }
        self.current += 1;
        true
    }

    fn peek(&self) -> char {
        if self.is_at_end() {
            '\0'
        } else {
            self.source.chars().nth(self.current).unwrap_or('\0')
        }
    }

    fn advance(&mut self) -> char {
        let c = self.source.chars().nth(self.current).unwrap_or('\0');
        self.current += 1;
        c
    }

    fn add_token(&mut self, kind: TokenKind) {
        let lexeme = self.source[self.start..self.current].to_string();
        let span = Span::new(self.start, self.current);
        self.tokens.push(Token::new(kind, span, lexeme));
    }

    fn is_at_end(&self) -> bool {
        self.current >= self.source.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scanner_numbers() {
        let mut scanner = Scanner::new("42 123");
        let tokens = scanner.scan_tokens().unwrap();
        assert_eq!(tokens.len(), 3); // 2 numbers + EOF
    }

    #[test]
    fn test_scanner_operators() {
        let mut scanner = Scanner::new("+ - * / == !=");
        let tokens = scanner.scan_tokens().unwrap();
        assert!(tokens.len() > 0);
    }
}
