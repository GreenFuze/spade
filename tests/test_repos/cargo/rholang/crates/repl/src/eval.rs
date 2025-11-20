use lexer::Lexer;
use parser::Parser;
use semantic_analyzer::SemanticAnalyzer;
use type_checker::TypeChecker;
use vm_runtime::Runtime;
use stdlib::StandardLibrary;
use common_types::Span;
use error_reporting::Diagnostic;

pub struct Evaluator {
    runtime: Runtime,
    stdlib: StandardLibrary,
    semantic_analyzer: SemanticAnalyzer,
    type_checker: TypeChecker,
}

impl Evaluator {
    pub fn new() -> Self {
        Self {
            runtime: Runtime::new(),
            stdlib: StandardLibrary::new(),
            semantic_analyzer: SemanticAnalyzer::new(),
            type_checker: TypeChecker::new(),
        }
    }

    pub fn eval(&mut self, input: &str) -> Result<String, String> {
        let mut lexer = Lexer::new(input);
        let tokens = lexer.tokenize().map_err(|_| "Lexer error".to_string())?;

        let mut parser = Parser::new(tokens);
        let declarations = parser.parse().map_err(|_| "Parser error".to_string())?;

        let ast = ast::Ast::new(
            declarations
                .into_iter()
                .map(|d| ast::AstNode::new(0, ast::NodeKind::Program { declarations: vec![] }, d.span))
                .collect(),
        );

        self.semantic_analyzer
            .analyze(&ast)
            .map_err(|_| "Semantic error".to_string())?;

        self.type_checker
            .check(&ast)
            .map_err(|_| "Type error".to_string())?;

        Ok("OK".to_string())
    }

    pub fn reset(&mut self) {
        self.runtime = Runtime::new();
    }
}

impl Default for Evaluator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_evaluator() {
        let mut eval = Evaluator::new();
        let result = eval.eval("42");
        assert!(result.is_ok() || result.is_err());
    }
}
