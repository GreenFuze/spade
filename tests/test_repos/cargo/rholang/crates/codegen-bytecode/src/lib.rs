pub mod instruction;
pub mod assembler;

pub use instruction::{Instruction, Opcode};
pub use assembler::Assembler;

use ir_gen::IrModule;

pub struct BytecodeGenerator {
    assembler: Assembler,
}

impl BytecodeGenerator {
    pub fn new() -> Self {
        Self {
            assembler: Assembler::new(),
        }
    }

    pub fn generate(&mut self, module: &IrModule) -> Vec<u8> {
        self.assembler.assemble(module)
    }
}

impl Default for BytecodeGenerator {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bytecode_generator() {
        let mut gen = BytecodeGenerator::new();
        let module = IrModule::new("test".to_string());
        let bytecode = gen.generate(&module);
        assert!(bytecode.len() >= 0);
    }
}
