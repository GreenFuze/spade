use crate::ir::*;
use ast::{Ast, AstNode, NodeKind};
use ast::nodes::{BinaryOperator, UnaryOperator, LiteralValue};

pub struct Lowering {
    next_temp: usize,
    next_label: usize,
}

impl Lowering {
    pub fn new() -> Self {
        Self {
            next_temp: 0,
            next_label: 0,
        }
    }

    pub fn lower_ast(&mut self, ast: &Ast) -> Result<IrModule, String> {
        let mut module = IrModule::new("main".to_string());

        for node in &ast.root {
            match &node.kind {
                NodeKind::FunctionDecl {
                    name,
                    params,
                    body,
                    ..
                } => {
                    let function = self.lower_function(name, params, body)?;
                    module.add_function(function);
                }
                NodeKind::VariableDecl {
                    name,
                    initializer,
                    ..
                } => {
                    let global = IrGlobal {
                        name: name.clone(),
                        ty: IrType::Int,
                        initializer: None,
                    };
                    module.add_global(global);
                }
                _ => {}
            }
        }

        Ok(module)
    }

    fn lower_function(
        &mut self,
        name: &str,
        params: &[AstNode],
        body: &AstNode,
    ) -> Result<IrFunction, String> {
        let ir_params = params
            .iter()
            .map(|p| self.lower_param(p))
            .collect::<Result<Vec<_>, _>>()?;

        let mut function = IrFunction::new(name.to_string(), ir_params, IrType::Void);

        let mut entry_block = IrBlock::new("entry".to_string());
        self.lower_node_to_block(body, &mut entry_block)?;

        if entry_block.terminator.is_none() {
            entry_block.set_terminator(IrTerminator::Return(None));
        }

        function.add_block(entry_block);

        Ok(function)
    }

    fn lower_param(&self, node: &AstNode) -> Result<IrParam, String> {
        match &node.kind {
            NodeKind::Parameter { name, .. } => Ok(IrParam {
                name: name.clone(),
                ty: IrType::Int,
            }),
            _ => Err("Expected parameter node".to_string()),
        }
    }

    fn lower_node_to_block(
        &mut self,
        node: &AstNode,
        block: &mut IrBlock,
    ) -> Result<Option<IrValue>, String> {
        match &node.kind {
            NodeKind::Block { statements } => {
                let mut last_value = None;
                for stmt in statements {
                    last_value = self.lower_node_to_block(stmt, block)?;
                }
                Ok(last_value)
            }
            NodeKind::ExprStmt { expr } => self.lower_expr_to_block(expr, block),
            NodeKind::ReturnStmt { value } => {
                let ret_value = if let Some(val) = value {
                    self.lower_expr_to_block(val, block)?
                } else {
                    None
                };
                block.set_terminator(IrTerminator::Return(ret_value));
                Ok(None)
            }
            NodeKind::VariableDecl {
                name, initializer, ..
            } => {
                let value = if let Some(init) = initializer {
                    self.lower_expr_to_block(init, block)?
                } else {
                    None
                };

                if let Some(val) = value {
                    block.add_instruction(IrInstruction::Assign {
                        dest: name.clone(),
                        value: val,
                    });
                }
                Ok(None)
            }
            _ => self.lower_expr_to_block(node, block),
        }
    }

    fn lower_expr_to_block(
        &mut self,
        node: &AstNode,
        block: &mut IrBlock,
    ) -> Result<Option<IrValue>, String> {
        match &node.kind {
            NodeKind::Literal { value } => Ok(Some(self.lower_literal(value))),
            NodeKind::Identifier { name } => Ok(Some(IrValue::Variable(name.clone()))),
            NodeKind::BinaryExpr {
                left,
                operator,
                right,
            } => {
                let left_val = self
                    .lower_expr_to_block(left, block)?
                    .ok_or("Expected value")?;
                let right_val = self
                    .lower_expr_to_block(right, block)?
                    .ok_or("Expected value")?;

                let dest = self.fresh_temp();
                let op = self.lower_binary_op(operator);

                block.add_instruction(IrInstruction::Binary {
                    dest: dest.clone(),
                    op,
                    left: left_val,
                    right: right_val,
                });

                Ok(Some(IrValue::Variable(dest)))
            }
            NodeKind::UnaryExpr { operator, operand } => {
                let operand_val = self
                    .lower_expr_to_block(operand, block)?
                    .ok_or("Expected value")?;

                let dest = self.fresh_temp();
                let op = self.lower_unary_op(operator);

                block.add_instruction(IrInstruction::Unary {
                    dest: dest.clone(),
                    op,
                    operand: operand_val,
                });

                Ok(Some(IrValue::Variable(dest)))
            }
            NodeKind::CallExpr { callee, arguments } => {
                let callee_name = if let NodeKind::Identifier { name } = &callee.kind {
                    name.clone()
                } else {
                    return Err("Expected identifier for callee".to_string());
                };

                let mut arg_values = Vec::new();
                for arg in arguments {
                    if let Some(val) = self.lower_expr_to_block(arg, block)? {
                        arg_values.push(val);
                    }
                }

                let dest = self.fresh_temp();
                block.add_instruction(IrInstruction::Call {
                    dest: Some(dest.clone()),
                    callee: callee_name,
                    args: arg_values,
                });

                Ok(Some(IrValue::Variable(dest)))
            }
            _ => Ok(None),
        }
    }

    fn lower_literal(&self, value: &LiteralValue) -> IrValue {
        match value {
            LiteralValue::Integer(i) => IrValue::Constant(IrConstant::Int(*i)),
            LiteralValue::Float(f) => IrValue::Constant(IrConstant::Float(*f)),
            LiteralValue::String(s) => IrValue::Constant(IrConstant::String(s.clone())),
            LiteralValue::Boolean(b) => IrValue::Constant(IrConstant::Bool(*b)),
            LiteralValue::Unit => IrValue::Constant(IrConstant::Unit),
        }
    }

    fn lower_binary_op(&self, op: &BinaryOperator) -> IrBinaryOp {
        match op {
            BinaryOperator::Add => IrBinaryOp::Add,
            BinaryOperator::Subtract => IrBinaryOp::Sub,
            BinaryOperator::Multiply => IrBinaryOp::Mul,
            BinaryOperator::Divide => IrBinaryOp::Div,
            BinaryOperator::Equal => IrBinaryOp::Eq,
            BinaryOperator::NotEqual => IrBinaryOp::Ne,
            BinaryOperator::Less => IrBinaryOp::Lt,
            BinaryOperator::LessEqual => IrBinaryOp::Le,
            BinaryOperator::Greater => IrBinaryOp::Gt,
            BinaryOperator::GreaterEqual => IrBinaryOp::Ge,
            BinaryOperator::LogicalAnd => IrBinaryOp::Eq,
            BinaryOperator::LogicalOr => IrBinaryOp::Ne,
        }
    }

    fn lower_unary_op(&self, op: &UnaryOperator) -> IrUnaryOp {
        match op {
            UnaryOperator::Negate => IrUnaryOp::Neg,
            UnaryOperator::LogicalNot => IrUnaryOp::Not,
        }
    }

    fn fresh_temp(&mut self) -> String {
        let temp = format!("t{}", self.next_temp);
        self.next_temp += 1;
        temp
    }

    fn fresh_label(&mut self) -> String {
        let label = format!("L{}", self.next_label);
        self.next_label += 1;
        label
    }
}

impl Default for Lowering {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lowering() {
        let mut lowering = Lowering::new();
        let ast = Ast::empty();
        let result = lowering.lower_ast(&ast);
        assert!(result.is_ok());
    }

    #[test]
    fn test_fresh_temp() {
        let mut lowering = Lowering::new();
        let temp1 = lowering.fresh_temp();
        let temp2 = lowering.fresh_temp();
        assert_ne!(temp1, temp2);
        assert_eq!(temp1, "t0");
        assert_eq!(temp2, "t1");
    }
}
