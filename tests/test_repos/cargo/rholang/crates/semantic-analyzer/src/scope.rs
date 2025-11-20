use common_types::Span;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct ScopeId(usize);

impl ScopeId {
    pub fn new(id: usize) -> Self {
        Self(id)
    }

    pub fn as_usize(&self) -> usize {
        self.0
    }
}

#[derive(Debug, Clone)]
pub struct Symbol {
    pub name: String,
    pub kind: SymbolKind,
    pub span: Span,
    pub scope_id: ScopeId,
}

#[derive(Debug, Clone)]
pub enum SymbolKind {
    Variable,
    Function,
    Parameter,
    Type,
    Module,
}

#[derive(Debug)]
pub struct Scope {
    pub id: ScopeId,
    pub parent: Option<ScopeId>,
    pub symbols: HashMap<String, Symbol>,
    pub children: Vec<ScopeId>,
}

impl Scope {
    pub fn new(id: ScopeId, parent: Option<ScopeId>) -> Self {
        Self {
            id,
            parent,
            symbols: HashMap::new(),
            children: Vec::new(),
        }
    }

    pub fn define(&mut self, name: String, kind: SymbolKind, span: Span) {
        let symbol = Symbol {
            name: name.clone(),
            kind,
            span,
            scope_id: self.id,
        };
        self.symbols.insert(name, symbol);
    }

    pub fn lookup(&self, name: &str) -> Option<&Symbol> {
        self.symbols.get(name)
    }

    pub fn add_child(&mut self, child_id: ScopeId) {
        self.children.push(child_id);
    }
}

pub struct ScopeTree {
    scopes: Vec<Scope>,
    current: ScopeId,
}

impl ScopeTree {
    pub fn new() -> Self {
        let root_scope = Scope::new(ScopeId(0), None);
        Self {
            scopes: vec![root_scope],
            current: ScopeId(0),
        }
    }

    pub fn enter_scope(&mut self) -> ScopeId {
        let new_id = ScopeId(self.scopes.len());
        let new_scope = Scope::new(new_id, Some(self.current));

        if let Some(parent) = self.scopes.get_mut(self.current.0) {
            parent.add_child(new_id);
        }

        self.scopes.push(new_scope);
        self.current = new_id;
        new_id
    }

    pub fn exit_scope(&mut self) {
        if let Some(scope) = self.scopes.get(self.current.0) {
            if let Some(parent) = scope.parent {
                self.current = parent;
            }
        }
    }

    pub fn current_scope(&self) -> &Scope {
        &self.scopes[self.current.0]
    }

    pub fn current_scope_mut(&mut self) -> &mut Scope {
        &mut self.scopes[self.current.0]
    }

    pub fn get_scope(&self, id: ScopeId) -> Option<&Scope> {
        self.scopes.get(id.0)
    }

    pub fn lookup(&self, name: &str) -> Option<&Symbol> {
        let mut current = Some(self.current);

        while let Some(scope_id) = current {
            if let Some(scope) = self.get_scope(scope_id) {
                if let Some(symbol) = scope.lookup(name) {
                    return Some(symbol);
                }
                current = scope.parent;
            } else {
                break;
            }
        }

        None
    }
}

impl Default for ScopeTree {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scope_basic() {
        let mut scope = Scope::new(ScopeId(0), None);
        scope.define("x".to_string(), SymbolKind::Variable, Span::new(0, 1));
        assert!(scope.lookup("x").is_some());
        assert!(scope.lookup("y").is_none());
    }

    #[test]
    fn test_scope_tree() {
        let mut tree = ScopeTree::new();
        tree.current_scope_mut()
            .define("x".to_string(), SymbolKind::Variable, Span::new(0, 1));

        tree.enter_scope();
        tree.current_scope_mut()
            .define("y".to_string(), SymbolKind::Variable, Span::new(2, 3));

        assert!(tree.lookup("x").is_some());
        assert!(tree.lookup("y").is_some());

        tree.exit_scope();
        assert!(tree.lookup("x").is_some());
        assert!(tree.lookup("y").is_none());
    }
}
