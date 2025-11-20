use crate::c_types::CType;
use ir_gen::{IrModule, IrFunction, IrBlock, IrInstruction, IrValue, IrConstant, IrBinaryOp, IrUnaryOp, IrTerminator};

pub struct CEmitter {
    indent_level: usize,
}

impl CEmitter {
    pub fn new() -> Self {
        Self { indent_level: 0 }
    }

    pub fn emit_module(&mut self, module: &IrModule) -> String {
        let mut output = String::new();

        output.push_str("#include <stdio.h>\n");
        output.push_str("#include <stdlib.h>\n");
        output.push_str("#include <stdbool.h>\n\n");

        for global in &module.globals {
            let c_type = CType::from_ir_type(&global.ty);
            output.push_str(&format!("{} {};\n", c_type.to_string(), global.name));
        }

        if !module.globals.is_empty() {
            output.push('\n');
        }

        for function in &module.functions {
            output.push_str(&self.emit_function(function));
            output.push('\n');
        }

        output
    }

    fn emit_function(&mut self, function: &IrFunction) -> String {
        let mut output = String::new();

        let ret_type = CType::from_ir_type(&function.return_type);

        let params_str = if function.params.is_empty() {
            "void".to_string()
        } else {
            function
                .params
                .iter()
                .map(|p| {
                    let c_type = CType::from_ir_type(&p.ty);
                    format!("{} {}", c_type.to_string(), p.name)
                })
                .collect::<Vec<_>>()
                .join(", ")
        };

        output.push_str(&format!(
            "{} {}({}) {{\n",
            ret_type.to_string(),
            function.name,
            params_str
        ));

        self.indent_level += 1;

        for block in &function.blocks {
            output.push_str(&self.emit_block(block));
        }

        self.indent_level -= 1;

        output.push_str("}\n");

        output
    }

    fn emit_block(&mut self, block: &IrBlock) -> String {
        let mut output = String::new();

        if block.label != "entry" {
            output.push_str(&format!("{}:\n", block.label));
        }

        for instruction in &block.instructions {
            output.push_str(&self.emit_instruction(instruction));
        }

        if let Some(terminator) = &block.terminator {
            output.push_str(&self.emit_terminator(terminator));
        }

        output
    }

    fn emit_instruction(&self, instruction: &IrInstruction) -> String {
        let indent = "  ".repeat(self.indent_level);

        match instruction {
            IrInstruction::Assign { dest, value } => {
                format!(
                    "{}int {} = {};\n",
                    indent,
                    dest,
                    self.emit_value(value)
                )
            }
            IrInstruction::Binary {
                dest,
                op,
                left,
                right,
            } => {
                let op_str = self.emit_binary_op(*op);
                format!(
                    "{}int {} = {} {} {};\n",
                    indent,
                    dest,
                    self.emit_value(left),
                    op_str,
                    self.emit_value(right)
                )
            }
            IrInstruction::Unary { dest, op, operand } => {
                let op_str = self.emit_unary_op(*op);
                format!(
                    "{}int {} = {}{};\n",
                    indent,
                    dest,
                    op_str,
                    self.emit_value(operand)
                )
            }
            IrInstruction::Call {
                dest,
                callee,
                args,
            } => {
                let args_str = args
                    .iter()
                    .map(|a| self.emit_value(a))
                    .collect::<Vec<_>>()
                    .join(", ");

                if let Some(d) = dest {
                    format!("{}int {} = {}({});\n", indent, d, callee, args_str)
                } else {
                    format!("{}{}({});\n", indent, callee, args_str)
                }
            }
            IrInstruction::Load { dest, ptr } => {
                format!("{}int {} = *{};\n", indent, dest, ptr)
            }
            IrInstruction::Store { ptr, value } => {
                format!("{}*{} = {};\n", indent, ptr, self.emit_value(value))
            }
            IrInstruction::Alloca { dest, ty } => {
                let c_type = CType::from_ir_type(ty);
                format!("{}{}* {};\n", indent, c_type.to_string(), dest)
            }
        }
    }

    fn emit_terminator(&self, terminator: &IrTerminator) -> String {
        let indent = "  ".repeat(self.indent_level);

        match terminator {
            IrTerminator::Return(None) => format!("{}return;\n", indent),
            IrTerminator::Return(Some(value)) => {
                format!("{}return {};\n", indent, self.emit_value(value))
            }
            IrTerminator::Branch {
                condition,
                true_label,
                false_label,
            } => {
                format!(
                    "{}if ({}) goto {}; else goto {};\n",
                    indent,
                    self.emit_value(condition),
                    true_label,
                    false_label
                )
            }
            IrTerminator::Jump { target } => {
                format!("{}goto {};\n", indent, target)
            }
        }
    }

    fn emit_value(&self, value: &IrValue) -> String {
        match value {
            IrValue::Variable(name) => name.clone(),
            IrValue::Constant(constant) => self.emit_constant(constant),
        }
    }

    fn emit_constant(&self, constant: &IrConstant) -> String {
        match constant {
            IrConstant::Int(i) => i.to_string(),
            IrConstant::Float(f) => format!("{}f", f),
            IrConstant::Bool(b) => b.to_string(),
            IrConstant::String(s) => format!("\"{}\"", s),
            IrConstant::Unit => "0".to_string(),
        }
    }

    fn emit_binary_op(&self, op: IrBinaryOp) -> &'static str {
        match op {
            IrBinaryOp::Add => "+",
            IrBinaryOp::Sub => "-",
            IrBinaryOp::Mul => "*",
            IrBinaryOp::Div => "/",
            IrBinaryOp::Eq => "==",
            IrBinaryOp::Ne => "!=",
            IrBinaryOp::Lt => "<",
            IrBinaryOp::Le => "<=",
            IrBinaryOp::Gt => ">",
            IrBinaryOp::Ge => ">=",
        }
    }

    fn emit_unary_op(&self, op: IrUnaryOp) -> &'static str {
        match op {
            IrUnaryOp::Neg => "-",
            IrUnaryOp::Not => "!",
        }
    }
}

impl Default for CEmitter {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_emit_module() {
        let mut emitter = CEmitter::new();
        let module = IrModule::new("test".to_string());
        let code = emitter.emit_module(&module);
        assert!(code.contains("#include"));
    }

    #[test]
    fn test_emit_constant() {
        let emitter = CEmitter::new();
        assert_eq!(emitter.emit_constant(&IrConstant::Int(42)), "42");
        assert_eq!(emitter.emit_constant(&IrConstant::Bool(true)), "true");
    }
}
