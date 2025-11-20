pub mod passes;
pub mod dead_code;
pub mod constant_folding;

pub use passes::{OptimizationPass, PassManager};
pub use dead_code::DeadCodeElimination;
pub use constant_folding::ConstantFolding;

use ir_gen::IrModule;

pub struct Optimizer {
    pass_manager: PassManager,
}

impl Optimizer {
    pub fn new() -> Self {
        let mut pass_manager = PassManager::new();
        pass_manager.add_pass(Box::new(ConstantFolding::new()));
        pass_manager.add_pass(Box::new(DeadCodeElimination::new()));

        Self { pass_manager }
    }

    pub fn optimize(&mut self, module: &mut IrModule) {
        self.pass_manager.run(module);
    }
}

impl Default for Optimizer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_optimizer() {
        let mut optimizer = Optimizer::new();
        let mut module = IrModule::new("test".to_string());
        optimizer.optimize(&mut module);
    }
}
