use crate::{Stack, Heap};
use codegen_bytecode::instruction::{Value, Opcode};

#[derive(Debug)]
pub enum VMError {
    InvalidOpcode(u8),
    StackOverflow,
    StackUnderflow,
    InvalidAddress,
    DivisionByZero,
    OutOfBounds,
}

pub struct VM {
    stack: Stack,
    heap: Heap,
    bytecode: Vec<u8>,
    pc: usize,
    locals: Vec<Value>,
}

impl VM {
    pub fn new() -> Self {
        Self {
            stack: Stack::new(1024),
            heap: Heap::new(),
            bytecode: Vec::new(),
            pc: 0,
            locals: vec![Value::Unit; 256],
        }
    }

    pub fn load(&mut self, bytecode: &[u8]) {
        self.bytecode = bytecode.to_vec();
        self.pc = 0;
    }

    pub fn run(&mut self) -> Result<Option<Value>, VMError> {
        loop {
            if self.pc >= self.bytecode.len() {
                return Ok(None);
            }

            let opcode_byte = self.bytecode[self.pc];
            self.pc += 1;

            let opcode = Opcode::from_u8(opcode_byte)
                .ok_or(VMError::InvalidOpcode(opcode_byte))?;

            match opcode {
                Opcode::Nop => {}
                Opcode::Halt => return Ok(self.stack.peek().cloned()),

                Opcode::LoadConst => {
                    let value = self.read_value()?;
                    self.stack.push(value).map_err(|_| VMError::StackOverflow)?;
                }

                Opcode::LoadLocal => {
                    let idx = self.read_u16()? as usize;
                    if idx >= self.locals.len() {
                        return Err(VMError::OutOfBounds);
                    }
                    let value = self.locals[idx].clone();
                    self.stack.push(value).map_err(|_| VMError::StackOverflow)?;
                }

                Opcode::StoreLocal => {
                    let idx = self.read_u16()? as usize;
                    if idx >= self.locals.len() {
                        return Err(VMError::OutOfBounds);
                    }
                    let value = self.stack.pop().map_err(|_| VMError::StackUnderflow)?;
                    self.locals[idx] = value;
                }

                Opcode::Add => self.binary_op(|a, b| a + b)?,
                Opcode::Sub => self.binary_op(|a, b| a - b)?,
                Opcode::Mul => self.binary_op(|a, b| a * b)?,
                Opcode::Div => {
                    let b = self.pop_int()?;
                    if b == 0 {
                        return Err(VMError::DivisionByZero);
                    }
                    let a = self.pop_int()?;
                    self.stack.push(Value::Int(a / b)).map_err(|_| VMError::StackOverflow)?;
                }

                Opcode::Neg => {
                    let value = self.pop_int()?;
                    self.stack.push(Value::Int(-value)).map_err(|_| VMError::StackOverflow)?;
                }

                Opcode::Eq => self.comparison_op(|a, b| a == b)?,
                Opcode::Ne => self.comparison_op(|a, b| a != b)?,
                Opcode::Lt => self.comparison_op(|a, b| a < b)?,
                Opcode::Le => self.comparison_op(|a, b| a <= b)?,
                Opcode::Gt => self.comparison_op(|a, b| a > b)?,
                Opcode::Ge => self.comparison_op(|a, b| a >= b)?,

                Opcode::Not => {
                    let value = self.pop_bool()?;
                    self.stack.push(Value::Bool(!value)).map_err(|_| VMError::StackOverflow)?;
                }

                Opcode::Jump => {
                    let addr = self.read_u32()? as usize;
                    self.pc = addr;
                }

                Opcode::JumpIfTrue => {
                    let addr = self.read_u32()? as usize;
                    let cond = self.pop_bool()?;
                    if cond {
                        self.pc = addr;
                    }
                }

                Opcode::JumpIfFalse => {
                    let addr = self.read_u32()? as usize;
                    let cond = self.pop_bool()?;
                    if !cond {
                        self.pc = addr;
                    }
                }

                Opcode::Return => {
                    if self.stack.is_empty() {
                        return Ok(None);
                    }
                    let value = self.stack.pop().map_err(|_| VMError::StackUnderflow)?;
                    return Ok(Some(value));
                }

                Opcode::Pop => {
                    self.stack.pop().map_err(|_| VMError::StackUnderflow)?;
                }

                Opcode::Dup => {
                    let value = self.stack.peek().ok_or(VMError::StackUnderflow)?.clone();
                    self.stack.push(value).map_err(|_| VMError::StackOverflow)?;
                }

                _ => {}
            }
        }
    }

    fn binary_op<F>(&mut self, op: F) -> Result<(), VMError>
    where
        F: Fn(i64, i64) -> i64,
    {
        let b = self.pop_int()?;
        let a = self.pop_int()?;
        let result = op(a, b);
        self.stack.push(Value::Int(result)).map_err(|_| VMError::StackOverflow)?;
        Ok(())
    }

    fn comparison_op<F>(&mut self, op: F) -> Result<(), VMError>
    where
        F: Fn(i64, i64) -> bool,
    {
        let b = self.pop_int()?;
        let a = self.pop_int()?;
        let result = op(a, b);
        self.stack.push(Value::Bool(result)).map_err(|_| VMError::StackOverflow)?;
        Ok(())
    }

    fn pop_int(&mut self) -> Result<i64, VMError> {
        match self.stack.pop().map_err(|_| VMError::StackUnderflow)? {
            Value::Int(i) => Ok(i),
            _ => Err(VMError::InvalidOpcode(0)),
        }
    }

    fn pop_bool(&mut self) -> Result<bool, VMError> {
        match self.stack.pop().map_err(|_| VMError::StackUnderflow)? {
            Value::Bool(b) => Ok(b),
            _ => Err(VMError::InvalidOpcode(0)),
        }
    }

    fn read_u16(&mut self) -> Result<u16, VMError> {
        if self.pc + 2 > self.bytecode.len() {
            return Err(VMError::OutOfBounds);
        }
        let bytes = [self.bytecode[self.pc], self.bytecode[self.pc + 1]];
        self.pc += 2;
        Ok(u16::from_le_bytes(bytes))
    }

    fn read_u32(&mut self) -> Result<u32, VMError> {
        if self.pc + 4 > self.bytecode.len() {
            return Err(VMError::OutOfBounds);
        }
        let bytes = [
            self.bytecode[self.pc],
            self.bytecode[self.pc + 1],
            self.bytecode[self.pc + 2],
            self.bytecode[self.pc + 3],
        ];
        self.pc += 4;
        Ok(u32::from_le_bytes(bytes))
    }

    fn read_value(&mut self) -> Result<Value, VMError> {
        if self.pc >= self.bytecode.len() {
            return Err(VMError::OutOfBounds);
        }

        let value_type = self.bytecode[self.pc];
        self.pc += 1;

        match value_type {
            0x00 => Ok(Value::Unit),
            0x01 => {
                let bytes = self.read_bytes(8)?;
                let i = i64::from_le_bytes(bytes.try_into().unwrap());
                Ok(Value::Int(i))
            }
            0x02 => {
                let bytes = self.read_bytes(8)?;
                let f = f64::from_le_bytes(bytes.try_into().unwrap());
                Ok(Value::Float(f))
            }
            0x03 => {
                let b = self.bytecode[self.pc] != 0;
                self.pc += 1;
                Ok(Value::Bool(b))
            }
            _ => Err(VMError::InvalidOpcode(value_type)),
        }
    }

    fn read_bytes(&mut self, count: usize) -> Result<Vec<u8>, VMError> {
        if self.pc + count > self.bytecode.len() {
            return Err(VMError::OutOfBounds);
        }
        let bytes = self.bytecode[self.pc..self.pc + count].to_vec();
        self.pc += count;
        Ok(bytes)
    }
}

impl Default for VM {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vm_halt() {
        let mut vm = VM::new();
        vm.load(&[0xFF]); // Halt
        let result = vm.run();
        assert!(result.is_ok());
    }
}
