use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[repr(u8)]
pub enum Opcode {
    Nop = 0x00,

    LoadConst = 0x10,
    LoadLocal = 0x11,
    StoreLocal = 0x12,
    LoadGlobal = 0x13,
    StoreGlobal = 0x14,

    Add = 0x20,
    Sub = 0x21,
    Mul = 0x22,
    Div = 0x23,
    Neg = 0x24,

    Eq = 0x30,
    Ne = 0x31,
    Lt = 0x32,
    Le = 0x33,
    Gt = 0x34,
    Ge = 0x35,
    Not = 0x36,

    Jump = 0x40,
    JumpIfTrue = 0x41,
    JumpIfFalse = 0x42,

    Call = 0x50,
    Return = 0x51,

    Pop = 0x60,
    Dup = 0x61,

    Halt = 0xFF,
}

impl Opcode {
    pub fn from_u8(byte: u8) -> Option<Self> {
        match byte {
            0x00 => Some(Opcode::Nop),
            0x10 => Some(Opcode::LoadConst),
            0x11 => Some(Opcode::LoadLocal),
            0x12 => Some(Opcode::StoreLocal),
            0x13 => Some(Opcode::LoadGlobal),
            0x14 => Some(Opcode::StoreGlobal),
            0x20 => Some(Opcode::Add),
            0x21 => Some(Opcode::Sub),
            0x22 => Some(Opcode::Mul),
            0x23 => Some(Opcode::Div),
            0x24 => Some(Opcode::Neg),
            0x30 => Some(Opcode::Eq),
            0x31 => Some(Opcode::Ne),
            0x32 => Some(Opcode::Lt),
            0x33 => Some(Opcode::Le),
            0x34 => Some(Opcode::Gt),
            0x35 => Some(Opcode::Ge),
            0x36 => Some(Opcode::Not),
            0x40 => Some(Opcode::Jump),
            0x41 => Some(Opcode::JumpIfTrue),
            0x42 => Some(Opcode::JumpIfFalse),
            0x50 => Some(Opcode::Call),
            0x51 => Some(Opcode::Return),
            0x60 => Some(Opcode::Pop),
            0x61 => Some(Opcode::Dup),
            0xFF => Some(Opcode::Halt),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Instruction {
    Nop,

    LoadConst(Value),
    LoadLocal(u16),
    StoreLocal(u16),
    LoadGlobal(u16),
    StoreGlobal(u16),

    Add,
    Sub,
    Mul,
    Div,
    Neg,

    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
    Not,

    Jump(u32),
    JumpIfTrue(u32),
    JumpIfFalse(u32),

    Call(u16),
    Return,

    Pop,
    Dup,

    Halt,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Value {
    Int(i64),
    Float(f64),
    Bool(bool),
    String(String),
    Unit,
}

impl Instruction {
    pub fn encode(&self) -> Vec<u8> {
        let mut bytes = Vec::new();

        match self {
            Instruction::Nop => bytes.push(Opcode::Nop as u8),
            Instruction::LoadConst(value) => {
                bytes.push(Opcode::LoadConst as u8);
                bytes.extend_from_slice(&Self::encode_value(value));
            }
            Instruction::LoadLocal(idx) => {
                bytes.push(Opcode::LoadLocal as u8);
                bytes.extend_from_slice(&idx.to_le_bytes());
            }
            Instruction::StoreLocal(idx) => {
                bytes.push(Opcode::StoreLocal as u8);
                bytes.extend_from_slice(&idx.to_le_bytes());
            }
            Instruction::LoadGlobal(idx) => {
                bytes.push(Opcode::LoadGlobal as u8);
                bytes.extend_from_slice(&idx.to_le_bytes());
            }
            Instruction::StoreGlobal(idx) => {
                bytes.push(Opcode::StoreGlobal as u8);
                bytes.extend_from_slice(&idx.to_le_bytes());
            }
            Instruction::Add => bytes.push(Opcode::Add as u8),
            Instruction::Sub => bytes.push(Opcode::Sub as u8),
            Instruction::Mul => bytes.push(Opcode::Mul as u8),
            Instruction::Div => bytes.push(Opcode::Div as u8),
            Instruction::Neg => bytes.push(Opcode::Neg as u8),
            Instruction::Eq => bytes.push(Opcode::Eq as u8),
            Instruction::Ne => bytes.push(Opcode::Ne as u8),
            Instruction::Lt => bytes.push(Opcode::Lt as u8),
            Instruction::Le => bytes.push(Opcode::Le as u8),
            Instruction::Gt => bytes.push(Opcode::Gt as u8),
            Instruction::Ge => bytes.push(Opcode::Ge as u8),
            Instruction::Not => bytes.push(Opcode::Not as u8),
            Instruction::Jump(addr) => {
                bytes.push(Opcode::Jump as u8);
                bytes.extend_from_slice(&addr.to_le_bytes());
            }
            Instruction::JumpIfTrue(addr) => {
                bytes.push(Opcode::JumpIfTrue as u8);
                bytes.extend_from_slice(&addr.to_le_bytes());
            }
            Instruction::JumpIfFalse(addr) => {
                bytes.push(Opcode::JumpIfFalse as u8);
                bytes.extend_from_slice(&addr.to_le_bytes());
            }
            Instruction::Call(argc) => {
                bytes.push(Opcode::Call as u8);
                bytes.extend_from_slice(&argc.to_le_bytes());
            }
            Instruction::Return => bytes.push(Opcode::Return as u8),
            Instruction::Pop => bytes.push(Opcode::Pop as u8),
            Instruction::Dup => bytes.push(Opcode::Dup as u8),
            Instruction::Halt => bytes.push(Opcode::Halt as u8),
        }

        bytes
    }

    fn encode_value(value: &Value) -> Vec<u8> {
        match value {
            Value::Int(i) => {
                let mut bytes = vec![0x01];
                bytes.extend_from_slice(&i.to_le_bytes());
                bytes
            }
            Value::Float(f) => {
                let mut bytes = vec![0x02];
                bytes.extend_from_slice(&f.to_le_bytes());
                bytes
            }
            Value::Bool(b) => vec![0x03, if *b { 1 } else { 0 }],
            Value::String(s) => {
                let mut bytes = vec![0x04];
                let len = s.len() as u32;
                bytes.extend_from_slice(&len.to_le_bytes());
                bytes.extend_from_slice(s.as_bytes());
                bytes
            }
            Value::Unit => vec![0x00],
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_opcode_conversion() {
        assert_eq!(Opcode::from_u8(0x00), Some(Opcode::Nop));
        assert_eq!(Opcode::from_u8(0x20), Some(Opcode::Add));
        assert_eq!(Opcode::from_u8(0xFF), Some(Opcode::Halt));
    }

    #[test]
    fn test_instruction_encode() {
        let inst = Instruction::Nop;
        let bytes = inst.encode();
        assert_eq!(bytes, vec![0x00]);
    }

    #[test]
    fn test_instruction_encode_with_operand() {
        let inst = Instruction::LoadLocal(42);
        let bytes = inst.encode();
        assert_eq!(bytes[0], Opcode::LoadLocal as u8);
    }
}
