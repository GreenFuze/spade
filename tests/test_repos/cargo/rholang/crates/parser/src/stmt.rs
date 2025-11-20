use common_types::Span;
use crate::expr::Expr;

#[derive(Debug, Clone)]
pub struct Stmt {
    pub kind: StmtKind,
    pub span: Span,
}

#[derive(Debug, Clone)]
pub enum StmtKind {
    Expr(Expr),
    Let {
        name: String,
        value: Expr,
    },
    Return(Option<Expr>),
    While {
        condition: Expr,
        body: Box<Stmt>,
    },
    For {
        init: Box<Stmt>,
        condition: Expr,
        increment: Expr,
        body: Box<Stmt>,
    },
    If {
        condition: Expr,
        then_branch: Box<Stmt>,
        else_branch: Option<Box<Stmt>>,
    },
    Block(Vec<Stmt>),
}

impl Stmt {
    pub fn new(kind: StmtKind, span: Span) -> Self {
        Self { kind, span }
    }

    pub fn expr(expr: Expr, span: Span) -> Self {
        Self::new(StmtKind::Expr(expr), span)
    }

    pub fn block(stmts: Vec<Stmt>, span: Span) -> Self {
        Self::new(StmtKind::Block(stmts), span)
    }
}
