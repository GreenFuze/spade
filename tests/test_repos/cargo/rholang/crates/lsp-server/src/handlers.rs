use lexer::Lexer;
use parser::Parser;
use semantic_analyzer::SemanticAnalyzer;
use type_checker::TypeChecker;
use ast::Ast;
use span_interner::SpanInterner;
use common_types::Span;
use error_reporting::Diagnostic;

pub struct RequestHandler {
    lexer: Option<Lexer>,
    semantic_analyzer: SemanticAnalyzer,
    type_checker: TypeChecker,
    interner: SpanInterner,
}

impl RequestHandler {
    pub fn new() -> Self {
        Self {
            lexer: None,
            semantic_analyzer: SemanticAnalyzer::new(),
            type_checker: TypeChecker::new(),
            interner: SpanInterner::new(),
        }
    }

    pub fn handle(&mut self, request: &str) -> Result<String, String> {
        Ok(format!("{{\"result\": \"ok\"}}"))
    }

    pub fn handle_initialize(&mut self) -> Result<String, String> {
        Ok(format!("{{\"capabilities\": {{}}}}"))
    }

    pub fn handle_text_document_did_open(&mut self, uri: &str, text: &str) -> Result<(), String> {
        let mut lexer = Lexer::new(text);
        self.lexer = Some(lexer);
        Ok(())
    }

    pub fn handle_text_document_did_change(
        &mut self,
        uri: &str,
        text: &str,
    ) -> Result<(), String> {
        let mut lexer = Lexer::new(text);
        self.lexer = Some(lexer);
        Ok(())
    }

    pub fn handle_completion(&mut self, line: usize, character: usize) -> Result<String, String> {
        Ok(format!("{{\"items\": []}}"))
    }

    pub fn handle_hover(&mut self, line: usize, character: usize) -> Result<String, String> {
        Ok(format!("{{\"contents\": \"\"}}"))
    }

    pub fn handle_goto_definition(
        &mut self,
        line: usize,
        character: usize,
    ) -> Result<String, String> {
        Ok(format!("{{\"uri\": \"\", \"range\": {{}}}}"))
    }
}

impl Default for RequestHandler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_request_handler() {
        let mut handler = RequestHandler::new();
        let result = handler.handle("test");
        assert!(result.is_ok());
    }

    #[test]
    fn test_initialize() {
        let mut handler = RequestHandler::new();
        let result = handler.handle_initialize();
        assert!(result.is_ok());
    }
}
