pub mod inference;
pub mod unification;

pub use inference::{TypeInference, TypeVar};
pub use unification::{Unification, Substitution};

use ast::Ast;
use common_types::Span;
use error_reporting::Diagnostic;

#[derive(Debug, Clone, PartialEq)]
pub enum Type {
    Int,
    Float,
    Bool,
    String,
    Unit,
    Var(TypeVar),
    Function {
        params: Vec<Type>,
        ret: Box<Type>,
    },
    Tuple(Vec<Type>),
    Custom(String),
}

pub struct TypeChecker {
    inference: TypeInference,
}

impl TypeChecker {
    pub fn new() -> Self {
        Self {
            inference: TypeInference::new(),
        }
    }

    pub fn check(&mut self, ast: &Ast) -> Result<(), Vec<Diagnostic>> {
        self.inference.infer(ast)
    }

    pub fn get_type(&self, node_id: usize) -> Option<&Type> {
        self.inference.get_type(node_id)
    }
}

impl Default for TypeChecker {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_type_checker() {
        let mut checker = TypeChecker::new();
        let ast = Ast::empty();
        let result = checker.check(&ast);
        assert!(result.is_ok());
    }
}
