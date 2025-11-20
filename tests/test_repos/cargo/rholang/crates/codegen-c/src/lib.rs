pub mod emitter;
pub mod c_types;

pub use emitter::CEmitter;
pub use c_types::CType;

use ir_gen::IrModule;

pub struct CCodegen {
    emitter: CEmitter,
}

impl CCodegen {
    pub fn new() -> Self {
        Self {
            emitter: CEmitter::new(),
        }
    }

    pub fn generate(&mut self, module: &IrModule) -> String {
        self.emitter.emit_module(module)
    }
}

impl Default for CCodegen {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_codegen() {
        let mut codegen = CCodegen::new();
        let module = IrModule::new("test".to_string());
        let code = codegen.generate(&module);
        assert!(!code.is_empty());
    }
}
