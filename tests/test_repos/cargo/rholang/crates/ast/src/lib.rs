pub mod nodes;
pub mod visitor;
pub mod pretty_print;

pub use nodes::{AstNode, NodeId};
pub use visitor::{Visitor, VisitorMut};
pub use pretty_print::PrettyPrinter;

use common_types::Span;

#[derive(Debug, Clone)]
pub struct Ast {
    pub root: Vec<AstNode>,
}

impl Ast {
    pub fn new(root: Vec<AstNode>) -> Self {
        Self { root }
    }

    pub fn empty() -> Self {
        Self { root: Vec::new() }
    }

    pub fn accept<V: Visitor>(&self, visitor: &mut V) {
        for node in &self.root {
            node.accept(visitor);
        }
    }

    pub fn accept_mut<V: VisitorMut>(&mut self, visitor: &mut V) {
        for node in &mut self.root {
            node.accept_mut(visitor);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ast_creation() {
        let ast = Ast::empty();
        assert_eq!(ast.root.len(), 0);
    }
}
