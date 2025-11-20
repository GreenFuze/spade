pub mod scope;
pub mod resolver;

pub use scope::{Scope, ScopeId, Symbol};
pub use resolver::Resolver;

use ast::Ast;
use common_types::Span;
use error_reporting::Diagnostic;

pub struct SemanticAnalyzer {
    resolver: Resolver,
}

impl SemanticAnalyzer {
    pub fn new() -> Self {
        Self {
            resolver: Resolver::new(),
        }
    }

    pub fn analyze(&mut self, ast: &Ast) -> Result<(), Vec<Diagnostic>> {
        self.resolver.resolve(ast)
    }

    pub fn get_scope(&self, id: ScopeId) -> Option<&Scope> {
        self.resolver.get_scope(id)
    }
}

impl Default for SemanticAnalyzer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_semantic_analyzer() {
        let mut analyzer = SemanticAnalyzer::new();
        let ast = Ast::empty();
        let result = analyzer.analyze(&ast);
        assert!(result.is_ok());
    }
}
