use common_types::Span;
use crate::{expr::Expr, stmt::Stmt};

#[derive(Debug, Clone)]
pub struct Decl {
    pub kind: DeclKind,
    pub span: Span,
}

#[derive(Debug, Clone)]
pub enum DeclKind {
    Function {
        name: String,
        params: Vec<Parameter>,
        return_type: Option<Type>,
        body: Vec<Stmt>,
    },
    Let {
        name: String,
        type_annotation: Option<Type>,
        value: Option<Expr>,
    },
    Struct {
        name: String,
        fields: Vec<Field>,
    },
    Enum {
        name: String,
        variants: Vec<Variant>,
    },
    Type {
        name: String,
        type_def: Type,
    },
    Import {
        path: Vec<String>,
    },
}

#[derive(Debug, Clone)]
pub struct Parameter {
    pub name: String,
    pub ty: Type,
    pub span: Span,
}

#[derive(Debug, Clone)]
pub struct Field {
    pub name: String,
    pub ty: Type,
    pub span: Span,
}

#[derive(Debug, Clone)]
pub struct Variant {
    pub name: String,
    pub fields: Vec<Field>,
    pub span: Span,
}

#[derive(Debug, Clone)]
pub enum Type {
    Named(String),
    Function {
        params: Vec<Type>,
        return_type: Box<Type>,
    },
    Tuple(Vec<Type>),
    Array {
        element: Box<Type>,
        size: Option<usize>,
    },
    Generic {
        name: String,
        args: Vec<Type>,
    },
}

impl Decl {
    pub fn new(kind: DeclKind, span: Span) -> Self {
        Self { kind, span }
    }

    pub fn function(
        name: String,
        params: Vec<Parameter>,
        return_type: Option<Type>,
        body: Vec<Stmt>,
        span: Span,
    ) -> Self {
        Self::new(
            DeclKind::Function {
                name,
                params,
                return_type,
                body,
            },
            span,
        )
    }
}
