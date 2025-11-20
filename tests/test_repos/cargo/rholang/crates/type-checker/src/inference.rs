use crate::{Type, unification::{Unification, Substitution}};
use ast::{Ast, AstNode, NodeKind};
use ast::nodes::{BinaryOperator, UnaryOperator, LiteralValue};
use ast::visitor::Visitor;
use common_types::Span;
use error_reporting::Diagnostic;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct TypeVar(usize);

impl TypeVar {
    pub fn new(id: usize) -> Self {
        Self(id)
    }

    pub fn id(&self) -> usize {
        self.0
    }
}

pub struct TypeInference {
    type_map: HashMap<usize, Type>,
    next_var: usize,
    unification: Unification,
    errors: Vec<Diagnostic>,
}

impl TypeInference {
    pub fn new() -> Self {
        Self {
            type_map: HashMap::new(),
            next_var: 0,
            unification: Unification::new(),
            errors: Vec::new(),
        }
    }

    pub fn infer(&mut self, ast: &Ast) -> Result<(), Vec<Diagnostic>> {
        for node in &ast.root {
            self.infer_node(node);
        }

        if self.errors.is_empty() {
            Ok(())
        } else {
            Err(self.errors.clone())
        }
    }

    pub fn get_type(&self, node_id: usize) -> Option<&Type> {
        self.type_map.get(&node_id)
    }

    fn fresh_type_var(&mut self) -> TypeVar {
        let var = TypeVar(self.next_var);
        self.next_var += 1;
        var
    }

    fn infer_node(&mut self, node: &AstNode) -> Type {
        let ty = match &node.kind {
            NodeKind::Literal { value } => self.infer_literal(value),
            NodeKind::Identifier { .. } => Type::Var(self.fresh_type_var()),
            NodeKind::BinaryExpr {
                left,
                operator,
                right,
            } => self.infer_binary(left, operator, right),
            NodeKind::UnaryExpr { operator, operand } => self.infer_unary(operator, operand),
            NodeKind::CallExpr { callee, arguments } => {
                self.infer_call(callee, arguments)
            }
            NodeKind::FunctionDecl { params, body, .. } => {
                let param_types: Vec<Type> = params
                    .iter()
                    .map(|p| self.infer_node(p))
                    .collect();
                let ret_type = self.infer_node(body);
                Type::Function {
                    params: param_types,
                    ret: Box::new(ret_type),
                }
            }
            NodeKind::Block { statements } => {
                let mut last_type = Type::Unit;
                for stmt in statements {
                    last_type = self.infer_node(stmt);
                }
                last_type
            }
            _ => Type::Var(self.fresh_type_var()),
        };

        self.type_map.insert(node.id, ty.clone());
        ty
    }

    fn infer_literal(&self, value: &LiteralValue) -> Type {
        match value {
            LiteralValue::Integer(_) => Type::Int,
            LiteralValue::Float(_) => Type::Float,
            LiteralValue::String(_) => Type::String,
            LiteralValue::Boolean(_) => Type::Bool,
            LiteralValue::Unit => Type::Unit,
        }
    }

    fn infer_binary(&mut self, left: &AstNode, op: &BinaryOperator, right: &AstNode) -> Type {
        let left_ty = self.infer_node(left);
        let right_ty = self.infer_node(right);

        match op {
            BinaryOperator::Add
            | BinaryOperator::Subtract
            | BinaryOperator::Multiply
            | BinaryOperator::Divide => {
                // Arithmetic operations
                Type::Int
            }
            BinaryOperator::Equal
            | BinaryOperator::NotEqual
            | BinaryOperator::Less
            | BinaryOperator::LessEqual
            | BinaryOperator::Greater
            | BinaryOperator::GreaterEqual => {
                // Comparison operations
                Type::Bool
            }
            BinaryOperator::LogicalAnd | BinaryOperator::LogicalOr => {
                // Logical operations
                Type::Bool
            }
        }
    }

    fn infer_unary(&mut self, op: &UnaryOperator, operand: &AstNode) -> Type {
        let operand_ty = self.infer_node(operand);

        match op {
            UnaryOperator::Negate => Type::Int,
            UnaryOperator::LogicalNot => Type::Bool,
        }
    }

    fn infer_call(&mut self, callee: &AstNode, arguments: &[AstNode]) -> Type {
        let callee_ty = self.infer_node(callee);
        let arg_types: Vec<Type> = arguments.iter().map(|a| self.infer_node(a)).collect();

        Type::Var(self.fresh_type_var())
    }
}

impl Default for TypeInference {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_type_inference() {
        let mut inference = TypeInference::new();
        let ast = Ast::empty();
        let result = inference.infer(&ast);
        assert!(result.is_ok());
    }

    #[test]
    fn test_fresh_type_var() {
        let mut inference = TypeInference::new();
        let var1 = inference.fresh_type_var();
        let var2 = inference.fresh_type_var();
        assert_ne!(var1, var2);
    }
}
