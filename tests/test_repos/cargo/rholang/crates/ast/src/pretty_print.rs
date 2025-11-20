use crate::nodes::{AstNode, NodeKind, LiteralValue, BinaryOperator, UnaryOperator};
use crate::visitor::Visitor;

pub struct PrettyPrinter {
    output: String,
    indent_level: usize,
}

impl PrettyPrinter {
    pub fn new() -> Self {
        Self {
            output: String::new(),
            indent_level: 0,
        }
    }

    pub fn print(&mut self, node: &AstNode) -> String {
        self.visit_node(node);
        self.output.clone()
    }

    fn write_indent(&mut self) {
        for _ in 0..self.indent_level {
            self.output.push_str("  ");
        }
    }

    fn write_line(&mut self, text: &str) {
        self.write_indent();
        self.output.push_str(text);
        self.output.push('\n');
    }

    fn indent(&mut self) {
        self.indent_level += 1;
    }

    fn dedent(&mut self) {
        if self.indent_level > 0 {
            self.indent_level -= 1;
        }
    }
}

impl Default for PrettyPrinter {
    fn default() -> Self {
        Self::new()
    }
}

impl Visitor for PrettyPrinter {
    fn visit_node(&mut self, node: &AstNode) {
        match &node.kind {
            NodeKind::Program { declarations } => {
                self.write_line("Program {");
                self.indent();
                for decl in declarations {
                    self.visit_node(decl);
                }
                self.dedent();
                self.write_line("}");
            }
            NodeKind::FunctionDecl {
                name,
                params,
                return_type,
                body,
            } => {
                self.write_line(&format!("FunctionDecl '{}' {{", name));
                self.indent();
                self.write_line("params:");
                self.indent();
                for param in params {
                    self.visit_node(param);
                }
                self.dedent();
                if let Some(ret) = return_type {
                    self.write_line("return_type:");
                    self.indent();
                    self.visit_node(ret);
                    self.dedent();
                }
                self.write_line("body:");
                self.indent();
                self.visit_node(body);
                self.dedent();
                self.dedent();
                self.write_line("}");
            }
            NodeKind::VariableDecl {
                name,
                type_annotation,
                initializer,
            } => {
                self.write_line(&format!("VariableDecl '{}' {{", name));
                self.indent();
                if let Some(ty) = type_annotation {
                    self.write_line("type:");
                    self.indent();
                    self.visit_node(ty);
                    self.dedent();
                }
                if let Some(init) = initializer {
                    self.write_line("initializer:");
                    self.indent();
                    self.visit_node(init);
                    self.dedent();
                }
                self.dedent();
                self.write_line("}");
            }
            NodeKind::Parameter { name, ty } => {
                self.write_line(&format!("Parameter '{}' {{", name));
                self.indent();
                self.visit_node(ty);
                self.dedent();
                self.write_line("}");
            }
            NodeKind::Block { statements } => {
                self.write_line("Block {");
                self.indent();
                for stmt in statements {
                    self.visit_node(stmt);
                }
                self.dedent();
                self.write_line("}");
            }
            NodeKind::ExprStmt { expr } => {
                self.write_line("ExprStmt {");
                self.indent();
                self.visit_node(expr);
                self.dedent();
                self.write_line("}");
            }
            NodeKind::IfStmt {
                condition,
                then_branch,
                else_branch,
            } => {
                self.write_line("IfStmt {");
                self.indent();
                self.write_line("condition:");
                self.indent();
                self.visit_node(condition);
                self.dedent();
                self.write_line("then:");
                self.indent();
                self.visit_node(then_branch);
                self.dedent();
                if let Some(else_br) = else_branch {
                    self.write_line("else:");
                    self.indent();
                    self.visit_node(else_br);
                    self.dedent();
                }
                self.dedent();
                self.write_line("}");
            }
            NodeKind::WhileStmt { condition, body } => {
                self.write_line("WhileStmt {");
                self.indent();
                self.write_line("condition:");
                self.indent();
                self.visit_node(condition);
                self.dedent();
                self.write_line("body:");
                self.indent();
                self.visit_node(body);
                self.dedent();
                self.dedent();
                self.write_line("}");
            }
            NodeKind::ReturnStmt { value } => {
                self.write_line("ReturnStmt {");
                if let Some(val) = value {
                    self.indent();
                    self.visit_node(val);
                    self.dedent();
                }
                self.write_line("}");
            }
            NodeKind::BinaryExpr {
                left,
                operator,
                right,
            } => {
                let op_str = match operator {
                    BinaryOperator::Add => "+",
                    BinaryOperator::Subtract => "-",
                    BinaryOperator::Multiply => "*",
                    BinaryOperator::Divide => "/",
                    BinaryOperator::Equal => "==",
                    BinaryOperator::NotEqual => "!=",
                    BinaryOperator::Less => "<",
                    BinaryOperator::LessEqual => "<=",
                    BinaryOperator::Greater => ">",
                    BinaryOperator::GreaterEqual => ">=",
                    BinaryOperator::LogicalAnd => "&&",
                    BinaryOperator::LogicalOr => "||",
                };
                self.write_line(&format!("BinaryExpr '{}' {{", op_str));
                self.indent();
                self.write_line("left:");
                self.indent();
                self.visit_node(left);
                self.dedent();
                self.write_line("right:");
                self.indent();
                self.visit_node(right);
                self.dedent();
                self.dedent();
                self.write_line("}");
            }
            NodeKind::UnaryExpr { operator, operand } => {
                let op_str = match operator {
                    UnaryOperator::Negate => "-",
                    UnaryOperator::LogicalNot => "!",
                };
                self.write_line(&format!("UnaryExpr '{}' {{", op_str));
                self.indent();
                self.visit_node(operand);
                self.dedent();
                self.write_line("}");
            }
            NodeKind::CallExpr { callee, arguments } => {
                self.write_line("CallExpr {");
                self.indent();
                self.write_line("callee:");
                self.indent();
                self.visit_node(callee);
                self.dedent();
                self.write_line("arguments:");
                self.indent();
                for arg in arguments {
                    self.visit_node(arg);
                }
                self.dedent();
                self.dedent();
                self.write_line("}");
            }
            NodeKind::Identifier { name } => {
                self.write_line(&format!("Identifier '{}'", name));
            }
            NodeKind::Literal { value } => {
                let val_str = match value {
                    LiteralValue::Integer(i) => format!("{}", i),
                    LiteralValue::Float(f) => format!("{}", f),
                    LiteralValue::String(s) => format!("\"{}\"", s),
                    LiteralValue::Boolean(b) => format!("{}", b),
                    LiteralValue::Unit => "()".to_string(),
                };
                self.write_line(&format!("Literal {}", val_str));
            }
            NodeKind::Type { name } => {
                self.write_line(&format!("Type '{}'", name));
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use common_types::Span;

    #[test]
    fn test_pretty_print_literal() {
        let node = AstNode::new(
            0,
            NodeKind::Literal {
                value: LiteralValue::Integer(42),
            },
            Span::new(0, 2),
        );
        let mut printer = PrettyPrinter::new();
        let output = printer.print(&node);
        assert!(output.contains("Literal 42"));
    }
}
