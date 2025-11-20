pub mod lower;
pub mod ir;

pub use lower::Lowering;
pub use ir::{IrModule, IrFunction, IrInstruction};

use ast::Ast;
use common_types::Span;

pub struct IrGenerator {
    lowering: Lowering,
}

impl IrGenerator {
    pub fn new() -> Self {
        Self {
            lowering: Lowering::new(),
        }
    }

    pub fn generate(&mut self, ast: &Ast) -> Result<IrModule, String> {
        self.lowering.lower_ast(ast)
    }
}

impl Default for IrGenerator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ir_generator() {
        let mut generator = IrGenerator::new();
        let ast = Ast::empty();
        let result = generator.generate(&ast);
        assert!(result.is_ok());
    }
}
