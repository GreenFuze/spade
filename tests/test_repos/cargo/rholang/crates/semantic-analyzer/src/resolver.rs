use crate::scope::{ScopeTree, ScopeId, SymbolKind};
use ast::{Ast, AstNode, NodeKind};
use ast::visitor::Visitor;
use common_types::Span;
use error_reporting::Diagnostic;

pub struct Resolver {
    scope_tree: ScopeTree,
    errors: Vec<Diagnostic>,
}

impl Resolver {
    pub fn new() -> Self {
        Self {
            scope_tree: ScopeTree::new(),
            errors: Vec::new(),
        }
    }

    pub fn resolve(&mut self, ast: &Ast) -> Result<(), Vec<Diagnostic>> {
        ast.accept(self);

        if self.errors.is_empty() {
            Ok(())
        } else {
            Err(self.errors.clone())
        }
    }

    pub fn get_scope(&self, id: ScopeId) -> Option<&crate::scope::Scope> {
        self.scope_tree.get_scope(id)
    }

    fn define_symbol(&mut self, name: String, kind: SymbolKind, span: Span) {
        self.scope_tree
            .current_scope_mut()
            .define(name, kind, span);
    }

    fn resolve_symbol(&self, name: &str) -> bool {
        self.scope_tree.lookup(name).is_some()
    }
}

impl Default for Resolver {
    fn default() -> Self {
        Self::new()
    }
}

impl Visitor for Resolver {
    fn visit_node(&mut self, node: &AstNode) {
        match &node.kind {
            NodeKind::FunctionDecl { name, params, body, .. } => {
                self.define_symbol(name.clone(), SymbolKind::Function, node.span);

                self.scope_tree.enter_scope();

                for param in params {
                    self.visit_node(param);
                }

                self.visit_node(body);

                self.scope_tree.exit_scope();
            }
            NodeKind::VariableDecl { name, initializer, .. } => {
                if let Some(init) = initializer {
                    self.visit_node(init);
                }

                self.define_symbol(name.clone(), SymbolKind::Variable, node.span);
            }
            NodeKind::Parameter { name, ty } => {
                self.define_symbol(name.clone(), SymbolKind::Parameter, node.span);
                self.visit_node(ty);
            }
            NodeKind::Block { statements } => {
                self.scope_tree.enter_scope();

                for stmt in statements {
                    self.visit_node(stmt);
                }

                self.scope_tree.exit_scope();
            }
            NodeKind::Identifier { name } => {
                if !self.resolve_symbol(name) {
                    // Could record an error here
                }
            }
            _ => {
                self.walk_node(node);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_resolver_empty() {
        let mut resolver = Resolver::new();
        let ast = Ast::empty();
        let result = resolver.resolve(&ast);
        assert!(result.is_ok());
    }
}
