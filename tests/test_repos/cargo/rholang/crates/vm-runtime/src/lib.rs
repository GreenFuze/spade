pub mod vm;
pub mod stack;
pub mod heap;

pub use vm::{VM, VMError};
pub use stack::Stack;
pub use heap::Heap;

use codegen_bytecode::instruction::Value;

pub struct Runtime {
    vm: VM,
}

impl Runtime {
    pub fn new() -> Self {
        Self { vm: VM::new() }
    }

    pub fn execute(&mut self, bytecode: &[u8]) -> Result<Option<Value>, VMError> {
        self.vm.load(bytecode);
        self.vm.run()
    }
}

impl Default for Runtime {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_runtime() {
        let mut runtime = Runtime::new();
        let bytecode = vec![0xFF]; // Halt
        let result = runtime.execute(&bytecode);
        assert!(result.is_ok());
    }
}
