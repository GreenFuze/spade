use crate::handlers::RequestHandler;
use std::io::{self, BufRead, Write};

pub struct LspServer {
    handler: RequestHandler,
}

impl LspServer {
    pub fn new() -> Self {
        Self {
            handler: RequestHandler::new(),
        }
    }

    pub fn run(&mut self) -> Result<(), String> {
        let stdin = io::stdin();
        let mut stdout = io::stdout();

        for line in stdin.lock().lines() {
            let line = line.map_err(|e| e.to_string())?;

            if line.is_empty() {
                continue;
            }

            let response = self.handle_request(&line)?;

            writeln!(stdout, "{}", response).map_err(|e| e.to_string())?;
            stdout.flush().map_err(|e| e.to_string())?;
        }

        Ok(())
    }

    fn handle_request(&mut self, request: &str) -> Result<String, String> {
        self.handler.handle(request)
    }
}

impl Default for LspServer {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone)]
pub struct Position {
    pub line: usize,
    pub character: usize,
}

#[derive(Debug, Clone)]
pub struct Range {
    pub start: Position,
    pub end: Position,
}

#[derive(Debug, Clone)]
pub struct TextDocumentIdentifier {
    pub uri: String,
}

#[derive(Debug, Clone)]
pub struct TextDocumentPositionParams {
    pub text_document: TextDocumentIdentifier,
    pub position: Position,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lsp_server_creation() {
        let server = LspServer::new();
        assert!(true);
    }
}
