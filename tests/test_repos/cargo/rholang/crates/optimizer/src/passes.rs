use ir_gen::IrModule;

pub trait OptimizationPass {
    fn name(&self) -> &str;
    fn run(&mut self, module: &mut IrModule) -> bool;
}

pub struct PassManager {
    passes: Vec<Box<dyn OptimizationPass>>,
}

impl PassManager {
    pub fn new() -> Self {
        Self { passes: Vec::new() }
    }

    pub fn add_pass(&mut self, pass: Box<dyn OptimizationPass>) {
        self.passes.push(pass);
    }

    pub fn run(&mut self, module: &mut IrModule) {
        let max_iterations = 10;
        let mut iteration = 0;

        loop {
            let mut changed = false;
            iteration += 1;

            for pass in &mut self.passes {
                if pass.run(module) {
                    changed = true;
                }
            }

            if !changed || iteration >= max_iterations {
                break;
            }
        }
    }
}

impl Default for PassManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct TestPass {
        run_count: usize,
    }

    impl TestPass {
        fn new() -> Self {
            Self { run_count: 0 }
        }
    }

    impl OptimizationPass for TestPass {
        fn name(&self) -> &str {
            "test_pass"
        }

        fn run(&mut self, _module: &mut IrModule) -> bool {
            self.run_count += 1;
            false
        }
    }

    #[test]
    fn test_pass_manager() {
        let mut manager = PassManager::new();
        manager.add_pass(Box::new(TestPass::new()));
        let mut module = IrModule::new("test".to_string());
        manager.run(&mut module);
    }
}
