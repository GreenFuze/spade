use crate::instruction::{Instruction, Value};
use ir_gen::{IrModule, IrFunction, IrBlock, IrInstruction, IrValue, IrConstant, IrBinaryOp, IrUnaryOp, IrTerminator};
use std::collections::HashMap;

pub struct Assembler {
    instructions: Vec<Instruction>,
    labels: HashMap<String, u32>,
    variables: HashMap<String, u16>,
    next_var: u16,
}

impl Assembler {
    pub fn new() -> Self {
        Self {
            instructions: Vec::new(),
            labels: HashMap::new(),
            variables: HashMap::new(),
            next_var: 0,
        }
    }

    pub fn assemble(&mut self, module: &IrModule) -> Vec<u8> {
        for function in &module.functions {
            self.assemble_function(function);
        }

        self.instructions.push(Instruction::Halt);

        let mut bytecode = Vec::new();
        for instruction in &self.instructions {
            bytecode.extend_from_slice(&instruction.encode());
        }

        bytecode
    }

    fn assemble_function(&mut self, function: &IrFunction) {
        for block in &function.blocks {
            self.assemble_block(block);
        }
    }

    fn assemble_block(&mut self, block: &IrBlock) {
        let current_addr = self.instructions.len() as u32;
        self.labels.insert(block.label.clone(), current_addr);

        for instruction in &block.instructions {
            self.assemble_instruction(instruction);
        }

        if let Some(terminator) = &block.terminator {
            self.assemble_terminator(terminator);
        }
    }

    fn assemble_instruction(&mut self, instruction: &IrInstruction) {
        match instruction {
            IrInstruction::Assign { dest, value } => {
                self.assemble_value(value);
                let var_idx = self.get_or_create_var(dest);
                self.instructions.push(Instruction::StoreLocal(var_idx));
            }
            IrInstruction::Binary {
                dest,
                op,
                left,
                right,
            } => {
                self.assemble_value(left);
                self.assemble_value(right);

                let inst = match op {
                    IrBinaryOp::Add => Instruction::Add,
                    IrBinaryOp::Sub => Instruction::Sub,
                    IrBinaryOp::Mul => Instruction::Mul,
                    IrBinaryOp::Div => Instruction::Div,
                    IrBinaryOp::Eq => Instruction::Eq,
                    IrBinaryOp::Ne => Instruction::Ne,
                    IrBinaryOp::Lt => Instruction::Lt,
                    IrBinaryOp::Le => Instruction::Le,
                    IrBinaryOp::Gt => Instruction::Gt,
                    IrBinaryOp::Ge => Instruction::Ge,
                };

                self.instructions.push(inst);

                let var_idx = self.get_or_create_var(dest);
                self.instructions.push(Instruction::StoreLocal(var_idx));
            }
            IrInstruction::Unary { dest, op, operand } => {
                self.assemble_value(operand);

                let inst = match op {
                    IrUnaryOp::Neg => Instruction::Neg,
                    IrUnaryOp::Not => Instruction::Not,
                };

                self.instructions.push(inst);

                let var_idx = self.get_or_create_var(dest);
                self.instructions.push(Instruction::StoreLocal(var_idx));
            }
            IrInstruction::Call {
                dest,
                callee,
                args,
            } => {
                for arg in args {
                    self.assemble_value(arg);
                }

                self.instructions.push(Instruction::Call(args.len() as u16));

                if let Some(d) = dest {
                    let var_idx = self.get_or_create_var(d);
                    self.instructions.push(Instruction::StoreLocal(var_idx));
                }
            }
            IrInstruction::Load { dest, ptr } => {
                let var_idx = self.get_or_create_var(ptr);
                self.instructions.push(Instruction::LoadLocal(var_idx));

                let dest_idx = self.get_or_create_var(dest);
                self.instructions.push(Instruction::StoreLocal(dest_idx));
            }
            IrInstruction::Store { ptr, value } => {
                self.assemble_value(value);

                let var_idx = self.get_or_create_var(ptr);
                self.instructions.push(Instruction::StoreLocal(var_idx));
            }
            IrInstruction::Alloca { dest, .. } => {
                self.instructions.push(Instruction::LoadConst(Value::Int(0)));

                let var_idx = self.get_or_create_var(dest);
                self.instructions.push(Instruction::StoreLocal(var_idx));
            }
        }
    }

    fn assemble_terminator(&mut self, terminator: &IrTerminator) {
        match terminator {
            IrTerminator::Return(None) => {
                self.instructions.push(Instruction::Return);
            }
            IrTerminator::Return(Some(value)) => {
                self.assemble_value(value);
                self.instructions.push(Instruction::Return);
            }
            IrTerminator::Branch {
                condition,
                true_label,
                false_label,
            } => {
                self.assemble_value(condition);

                let true_addr = *self.labels.get(true_label).unwrap_or(&0);
                self.instructions.push(Instruction::JumpIfTrue(true_addr));

                let false_addr = *self.labels.get(false_label).unwrap_or(&0);
                self.instructions.push(Instruction::Jump(false_addr));
            }
            IrTerminator::Jump { target } => {
                let addr = *self.labels.get(target).unwrap_or(&0);
                self.instructions.push(Instruction::Jump(addr));
            }
        }
    }

    fn assemble_value(&mut self, value: &IrValue) {
        match value {
            IrValue::Variable(name) => {
                let var_idx = self.get_or_create_var(name);
                self.instructions.push(Instruction::LoadLocal(var_idx));
            }
            IrValue::Constant(constant) => {
                let val = self.constant_to_value(constant);
                self.instructions.push(Instruction::LoadConst(val));
            }
        }
    }

    fn constant_to_value(&self, constant: &IrConstant) -> Value {
        match constant {
            IrConstant::Int(i) => Value::Int(*i),
            IrConstant::Float(f) => Value::Float(*f),
            IrConstant::Bool(b) => Value::Bool(*b),
            IrConstant::String(s) => Value::String(s.clone()),
            IrConstant::Unit => Value::Unit,
        }
    }

    fn get_or_create_var(&mut self, name: &str) -> u16 {
        if let Some(&idx) = self.variables.get(name) {
            idx
        } else {
            let idx = self.next_var;
            self.variables.insert(name.to_string(), idx);
            self.next_var += 1;
            idx
        }
    }
}

impl Default for Assembler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_assembler() {
        let mut assembler = Assembler::new();
        let module = IrModule::new("test".to_string());
        let bytecode = assembler.assemble(&module);
        assert!(!bytecode.is_empty());
    }

    #[test]
    fn test_get_or_create_var() {
        let mut assembler = Assembler::new();
        let idx1 = assembler.get_or_create_var("x");
        let idx2 = assembler.get_or_create_var("x");
        assert_eq!(idx1, idx2);

        let idx3 = assembler.get_or_create_var("y");
        assert_ne!(idx1, idx3);
    }
}
