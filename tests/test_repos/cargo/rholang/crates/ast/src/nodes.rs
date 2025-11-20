use common_types::Span;
use crate::visitor::{Visitor, VisitorMut};

pub type NodeId = usize;

#[derive(Debug, Clone)]
pub struct AstNode {
    pub id: NodeId,
    pub kind: NodeKind,
    pub span: Span,
}

#[derive(Debug, Clone)]
pub enum NodeKind {
    Program {
        declarations: Vec<AstNode>,
    },
    FunctionDecl {
        name: String,
        params: Vec<AstNode>,
        return_type: Option<Box<AstNode>>,
        body: Box<AstNode>,
    },
    VariableDecl {
        name: String,
        type_annotation: Option<Box<AstNode>>,
        initializer: Option<Box<AstNode>>,
    },
    Parameter {
        name: String,
        ty: Box<AstNode>,
    },
    Block {
        statements: Vec<AstNode>,
    },
    ExprStmt {
        expr: Box<AstNode>,
    },
    IfStmt {
        condition: Box<AstNode>,
        then_branch: Box<AstNode>,
        else_branch: Option<Box<AstNode>>,
    },
    WhileStmt {
        condition: Box<AstNode>,
        body: Box<AstNode>,
    },
    ReturnStmt {
        value: Option<Box<AstNode>>,
    },
    BinaryExpr {
        left: Box<AstNode>,
        operator: BinaryOperator,
        right: Box<AstNode>,
    },
    UnaryExpr {
        operator: UnaryOperator,
        operand: Box<AstNode>,
    },
    CallExpr {
        callee: Box<AstNode>,
        arguments: Vec<AstNode>,
    },
    Identifier {
        name: String,
    },
    Literal {
        value: LiteralValue,
    },
    Type {
        name: String,
    },
}

#[derive(Debug, Clone)]
pub enum BinaryOperator {
    Add,
    Subtract,
    Multiply,
    Divide,
    Equal,
    NotEqual,
    Less,
    LessEqual,
    Greater,
    GreaterEqual,
    LogicalAnd,
    LogicalOr,
}

#[derive(Debug, Clone)]
pub enum UnaryOperator {
    Negate,
    LogicalNot,
}

#[derive(Debug, Clone)]
pub enum LiteralValue {
    Integer(i64),
    Float(f64),
    String(String),
    Boolean(bool),
    Unit,
}

impl AstNode {
    pub fn new(id: NodeId, kind: NodeKind, span: Span) -> Self {
        Self { id, kind, span }
    }

    pub fn accept<V: Visitor>(&self, visitor: &mut V) {
        visitor.visit_node(self);
    }

    pub fn accept_mut<V: VisitorMut>(&mut self, visitor: &mut V) {
        visitor.visit_node_mut(self);
    }
}
