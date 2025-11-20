use crate::nodes::{AstNode, NodeKind};

pub trait Visitor {
    fn visit_node(&mut self, node: &AstNode) {
        self.walk_node(node);
    }

    fn walk_node(&mut self, node: &AstNode) {
        match &node.kind {
            NodeKind::Program { declarations } => {
                for decl in declarations {
                    self.visit_node(decl);
                }
            }
            NodeKind::FunctionDecl {
                params,
                return_type,
                body,
                ..
            } => {
                for param in params {
                    self.visit_node(param);
                }
                if let Some(ret) = return_type {
                    self.visit_node(ret);
                }
                self.visit_node(body);
            }
            NodeKind::VariableDecl {
                type_annotation,
                initializer,
                ..
            } => {
                if let Some(ty) = type_annotation {
                    self.visit_node(ty);
                }
                if let Some(init) = initializer {
                    self.visit_node(init);
                }
            }
            NodeKind::Parameter { ty, .. } => {
                self.visit_node(ty);
            }
            NodeKind::Block { statements } => {
                for stmt in statements {
                    self.visit_node(stmt);
                }
            }
            NodeKind::ExprStmt { expr } => {
                self.visit_node(expr);
            }
            NodeKind::IfStmt {
                condition,
                then_branch,
                else_branch,
            } => {
                self.visit_node(condition);
                self.visit_node(then_branch);
                if let Some(else_br) = else_branch {
                    self.visit_node(else_br);
                }
            }
            NodeKind::WhileStmt { condition, body } => {
                self.visit_node(condition);
                self.visit_node(body);
            }
            NodeKind::ReturnStmt { value } => {
                if let Some(val) = value {
                    self.visit_node(val);
                }
            }
            NodeKind::BinaryExpr { left, right, .. } => {
                self.visit_node(left);
                self.visit_node(right);
            }
            NodeKind::UnaryExpr { operand, .. } => {
                self.visit_node(operand);
            }
            NodeKind::CallExpr { callee, arguments } => {
                self.visit_node(callee);
                for arg in arguments {
                    self.visit_node(arg);
                }
            }
            NodeKind::Identifier { .. } | NodeKind::Literal { .. } | NodeKind::Type { .. } => {
                // Leaf nodes
            }
        }
    }
}

pub trait VisitorMut {
    fn visit_node_mut(&mut self, node: &mut AstNode) {
        self.walk_node_mut(node);
    }

    fn walk_node_mut(&mut self, node: &mut AstNode) {
        match &mut node.kind {
            NodeKind::Program { declarations } => {
                for decl in declarations {
                    self.visit_node_mut(decl);
                }
            }
            NodeKind::FunctionDecl {
                params,
                return_type,
                body,
                ..
            } => {
                for param in params {
                    self.visit_node_mut(param);
                }
                if let Some(ret) = return_type {
                    self.visit_node_mut(ret);
                }
                self.visit_node_mut(body);
            }
            NodeKind::VariableDecl {
                type_annotation,
                initializer,
                ..
            } => {
                if let Some(ty) = type_annotation {
                    self.visit_node_mut(ty);
                }
                if let Some(init) = initializer {
                    self.visit_node_mut(init);
                }
            }
            NodeKind::Parameter { ty, .. } => {
                self.visit_node_mut(ty);
            }
            NodeKind::Block { statements } => {
                for stmt in statements {
                    self.visit_node_mut(stmt);
                }
            }
            NodeKind::ExprStmt { expr } => {
                self.visit_node_mut(expr);
            }
            NodeKind::IfStmt {
                condition,
                then_branch,
                else_branch,
            } => {
                self.visit_node_mut(condition);
                self.visit_node_mut(then_branch);
                if let Some(else_br) = else_branch {
                    self.visit_node_mut(else_br);
                }
            }
            NodeKind::WhileStmt { condition, body } => {
                self.visit_node_mut(condition);
                self.visit_node_mut(body);
            }
            NodeKind::ReturnStmt { value } => {
                if let Some(val) = value {
                    self.visit_node_mut(val);
                }
            }
            NodeKind::BinaryExpr { left, right, .. } => {
                self.visit_node_mut(left);
                self.visit_node_mut(right);
            }
            NodeKind::UnaryExpr { operand, .. } => {
                self.visit_node_mut(operand);
            }
            NodeKind::CallExpr { callee, arguments } => {
                self.visit_node_mut(callee);
                for arg in arguments {
                    self.visit_node_mut(arg);
                }
            }
            NodeKind::Identifier { .. } | NodeKind::Literal { .. } | NodeKind::Type { .. } => {
                // Leaf nodes
            }
        }
    }
}
