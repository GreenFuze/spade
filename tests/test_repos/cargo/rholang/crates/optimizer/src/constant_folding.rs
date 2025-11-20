use crate::passes::OptimizationPass;
use ir_gen::{IrModule, IrInstruction, IrValue, IrConstant, IrBinaryOp};

pub struct ConstantFolding {
    changed: bool,
}

impl ConstantFolding {
    pub fn new() -> Self {
        Self { changed: false }
    }

    fn fold_binary(
        &self,
        op: IrBinaryOp,
        left: &IrConstant,
        right: &IrConstant,
    ) -> Option<IrConstant> {
        match (left, right) {
            (IrConstant::Int(l), IrConstant::Int(r)) => {
                let result = match op {
                    IrBinaryOp::Add => l + r,
                    IrBinaryOp::Sub => l - r,
                    IrBinaryOp::Mul => l * r,
                    IrBinaryOp::Div => {
                        if *r != 0 {
                            l / r
                        } else {
                            return None;
                        }
                    }
                    IrBinaryOp::Eq => return Some(IrConstant::Bool(l == r)),
                    IrBinaryOp::Ne => return Some(IrConstant::Bool(l != r)),
                    IrBinaryOp::Lt => return Some(IrConstant::Bool(l < r)),
                    IrBinaryOp::Le => return Some(IrConstant::Bool(l <= r)),
                    IrBinaryOp::Gt => return Some(IrConstant::Bool(l > r)),
                    IrBinaryOp::Ge => return Some(IrConstant::Bool(l >= r)),
                };
                Some(IrConstant::Int(result))
            }
            (IrConstant::Float(l), IrConstant::Float(r)) => {
                let result = match op {
                    IrBinaryOp::Add => l + r,
                    IrBinaryOp::Sub => l - r,
                    IrBinaryOp::Mul => l * r,
                    IrBinaryOp::Div => l / r,
                    IrBinaryOp::Eq => return Some(IrConstant::Bool(l == r)),
                    IrBinaryOp::Ne => return Some(IrConstant::Bool(l != r)),
                    IrBinaryOp::Lt => return Some(IrConstant::Bool(l < r)),
                    IrBinaryOp::Le => return Some(IrConstant::Bool(l <= r)),
                    IrBinaryOp::Gt => return Some(IrConstant::Bool(l > r)),
                    IrBinaryOp::Ge => return Some(IrConstant::Bool(l >= r)),
                };
                Some(IrConstant::Float(result))
            }
            (IrConstant::Bool(l), IrConstant::Bool(r)) => match op {
                IrBinaryOp::Eq => Some(IrConstant::Bool(l == r)),
                IrBinaryOp::Ne => Some(IrConstant::Bool(l != r)),
                _ => None,
            },
            _ => None,
        }
    }
}

impl Default for ConstantFolding {
    fn default() -> Self {
        Self::new()
    }
}

impl OptimizationPass for ConstantFolding {
    fn name(&self) -> &str {
        "constant_folding"
    }

    fn run(&mut self, module: &mut IrModule) -> bool {
        self.changed = false;

        for function in &mut module.functions {
            for block in &mut function.blocks {
                for instruction in &mut block.instructions {
                    match instruction {
                        IrInstruction::Binary {
                            dest,
                            op,
                            left,
                            right,
                        } => {
                            if let (IrValue::Constant(l), IrValue::Constant(r)) = (left, right) {
                                if let Some(result) = self.fold_binary(*op, l, r) {
                                    *instruction = IrInstruction::Assign {
                                        dest: dest.clone(),
                                        value: IrValue::Constant(result),
                                    };
                                    self.changed = true;
                                }
                            }
                        }
                        IrInstruction::Unary { dest, op, operand } => {
                            if let IrValue::Constant(c) = operand {
                                let result = match (op, c) {
                                    (ir_gen::IrUnaryOp::Neg, IrConstant::Int(i)) => {
                                        Some(IrConstant::Int(-i))
                                    }
                                    (ir_gen::IrUnaryOp::Neg, IrConstant::Float(f)) => {
                                        Some(IrConstant::Float(-f))
                                    }
                                    (ir_gen::IrUnaryOp::Not, IrConstant::Bool(b)) => {
                                        Some(IrConstant::Bool(!b))
                                    }
                                    _ => None,
                                };

                                if let Some(res) = result {
                                    *instruction = IrInstruction::Assign {
                                        dest: dest.clone(),
                                        value: IrValue::Constant(res),
                                    };
                                    self.changed = true;
                                }
                            }
                        }
                        _ => {}
                    }
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
    fn test_constant_folding() {
        let mut cf = ConstantFolding::new();
        let mut module = IrModule::new("test".to_string());
        let changed = cf.run(&mut module);
        assert!(!changed);
    }

    #[test]
    fn test_fold_binary() {
        let cf = ConstantFolding::new();
        let result = cf.fold_binary(
            IrBinaryOp::Add,
            &IrConstant::Int(1),
            &IrConstant::Int(2),
        );
        assert_eq!(result, Some(IrConstant::Int(3)));
    }
}
