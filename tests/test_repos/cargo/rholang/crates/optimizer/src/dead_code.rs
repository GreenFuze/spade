use crate::passes::OptimizationPass;
use ir_gen::{IrModule, IrInstruction};
use std::collections::HashSet;

pub struct DeadCodeElimination {
    changed: bool,
}

impl DeadCodeElimination {
    pub fn new() -> Self {
        Self { changed: false }
    }

    fn is_instruction_used(&self, dest: &str, used_vars: &HashSet<String>) -> bool {
        used_vars.contains(dest)
    }

    fn collect_used_variables(&self, module: &IrModule) -> HashSet<String> {
        let mut used = HashSet::new();

        for function in &module.functions {
            for block in &function.blocks {
                for instruction in &block.instructions {
                    match instruction {
                        IrInstruction::Binary { left, right, .. } => {
                            if let ir_gen::IrValue::Variable(name) = left {
                                used.insert(name.clone());
                            }
                            if let ir_gen::IrValue::Variable(name) = right {
                                used.insert(name.clone());
                            }
                        }
                        IrInstruction::Unary { operand, .. } => {
                            if let ir_gen::IrValue::Variable(name) = operand {
                                used.insert(name.clone());
                            }
                        }
                        IrInstruction::Assign { value, .. } => {
                            if let ir_gen::IrValue::Variable(name) = value {
                                used.insert(name.clone());
                            }
                        }
                        IrInstruction::Call { args, .. } => {
                            for arg in args {
                                if let ir_gen::IrValue::Variable(name) = arg {
                                    used.insert(name.clone());
                                }
                            }
                        }
                        IrInstruction::Store { value, .. } => {
                            if let ir_gen::IrValue::Variable(name) = value {
                                used.insert(name.clone());
                            }
                        }
                        _ => {}
                    }
                }

                if let Some(terminator) = &block.terminator {
                    match terminator {
                        ir_gen::IrTerminator::Return(Some(value)) => {
                            if let ir_gen::IrValue::Variable(name) = value {
                                used.insert(name.clone());
                            }
                        }
                        ir_gen::IrTerminator::Branch { condition, .. } => {
                            if let ir_gen::IrValue::Variable(name) = condition {
                                used.insert(name.clone());
                            }
                        }
                        _ => {}
                    }
                }
            }
        }

        used
    }
}

impl Default for DeadCodeElimination {
    fn default() -> Self {
        Self::new()
    }
}

impl OptimizationPass for DeadCodeElimination {
    fn name(&self) -> &str {
        "dead_code_elimination"
    }

    fn run(&mut self, module: &mut IrModule) -> bool {
        self.changed = false;
        let used_vars = self.collect_used_variables(module);

        for function in &mut module.functions {
            for block in &mut function.blocks {
                let original_len = block.instructions.len();

                block.instructions.retain(|inst| match inst {
                    IrInstruction::Assign { dest, .. }
                    | IrInstruction::Binary { dest, .. }
                    | IrInstruction::Unary { dest, .. }
                    | IrInstruction::Alloca { dest, .. } => {
                        self.is_instruction_used(dest, &used_vars)
                    }
                    IrInstruction::Call { dest: Some(dest), .. } => {
                        self.is_instruction_used(dest, &used_vars)
                    }
                    _ => true,
                });

                if block.instructions.len() < original_len {
                    self.changed = true;
                }
            }
        }

        self.changed
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dead_code_elimination() {
        let mut dce = DeadCodeElimination::new();
        let mut module = IrModule::new("test".to_string());
        let changed = dce.run(&mut module);
        assert!(!changed);
    }
}
