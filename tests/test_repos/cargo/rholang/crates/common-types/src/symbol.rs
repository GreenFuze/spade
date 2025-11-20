//! Symbol table and identifier management.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A unique identifier for symbols (variables, functions, etc.)
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct Symbol(pub usize);

impl Symbol {
    pub fn new(id: usize) -> Self {
        Symbol(id)
    }
}

/// Global symbol table for tracking identifiers
#[derive(Debug, Clone, Default)]
pub struct SymbolTable {
    symbols: HashMap<String, Symbol>,
    reverse: HashMap<Symbol, String>,
    next_id: usize,
}

impl SymbolTable {
    pub fn new() -> Self {
        SymbolTable {
            symbols: HashMap::new(),
            reverse: HashMap::new(),
            next_id: 0,
        }
    }

    pub fn intern(&mut self, name: &str) -> Symbol {
        if let Some(&symbol) = self.symbols.get(name) {
            return symbol;
        }

        let symbol = Symbol::new(self.next_id);
        self.next_id += 1;
        self.symbols.insert(name.to_string(), symbol);
        self.reverse.insert(symbol, name.to_string());
        symbol
    }

    pub fn get(&self, name: &str) -> Option<Symbol> {
        self.symbols.get(name).copied()
    }

    pub fn resolve(&self, symbol: Symbol) -> Option<&str> {
        self.reverse.get(&symbol).map(|s| s.as_str())
    }

    pub fn len(&self) -> usize {
        self.symbols.len()
    }

    pub fn is_empty(&self) -> bool {
        self.symbols.is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_symbol_interning() {
        let mut table = SymbolTable::new();
        let sym1 = table.intern("foo");
        let sym2 = table.intern("foo");
        let sym3 = table.intern("bar");

        assert_eq!(sym1, sym2);
        assert_ne!(sym1, sym3);
    }

    #[test]
    fn test_symbol_resolution() {
        let mut table = SymbolTable::new();
        let sym = table.intern("test");
        assert_eq!(table.resolve(sym), Some("test"));
    }

    #[test]
    fn test_symbol_table_len() {
        let mut table = SymbolTable::new();
        assert_eq!(table.len(), 0);
        table.intern("a");
        table.intern("b");
        table.intern("a"); // duplicate
        assert_eq!(table.len(), 2);
    }
}
