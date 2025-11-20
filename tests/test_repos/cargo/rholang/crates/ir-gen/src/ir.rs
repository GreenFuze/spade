use common_types::Span;

#[derive(Debug, Clone)]
pub struct IrModule {
    pub name: String,
    pub functions: Vec<IrFunction>,
    pub globals: Vec<IrGlobal>,
}

impl IrModule {
    pub fn new(name: String) -> Self {
        Self {
            name,
            functions: Vec::new(),
            globals: Vec::new(),
        }
    }

    pub fn add_function(&mut self, function: IrFunction) {
        self.functions.push(function);
    }

    pub fn add_global(&mut self, global: IrGlobal) {
        self.globals.push(global);
    }
}

#[derive(Debug, Clone)]
pub struct IrFunction {
    pub name: String,
    pub params: Vec<IrParam>,
    pub return_type: IrType,
    pub blocks: Vec<IrBlock>,
}

impl IrFunction {
    pub fn new(name: String, params: Vec<IrParam>, return_type: IrType) -> Self {
        Self {
            name,
            params,
            return_type,
            blocks: Vec::new(),
        }
    }

    pub fn add_block(&mut self, block: IrBlock) {
        self.blocks.push(block);
    }
}

#[derive(Debug, Clone)]
pub struct IrBlock {
    pub label: String,
    pub instructions: Vec<IrInstruction>,
    pub terminator: Option<IrTerminator>,
}

impl IrBlock {
    pub fn new(label: String) -> Self {
        Self {
            label,
            instructions: Vec::new(),
            terminator: None,
        }
    }

    pub fn add_instruction(&mut self, instruction: IrInstruction) {
        self.instructions.push(instruction);
    }

    pub fn set_terminator(&mut self, terminator: IrTerminator) {
        self.terminator = Some(terminator);
    }
}

#[derive(Debug, Clone)]
pub struct IrParam {
    pub name: String,
    pub ty: IrType,
}

#[derive(Debug, Clone)]
pub struct IrGlobal {
    pub name: String,
    pub ty: IrType,
    pub initializer: Option<IrValue>,
}

#[derive(Debug, Clone)]
pub enum IrInstruction {
    Assign {
        dest: String,
        value: IrValue,
    },
    Binary {
        dest: String,
        op: IrBinaryOp,
        left: IrValue,
        right: IrValue,
    },
    Unary {
        dest: String,
        op: IrUnaryOp,
        operand: IrValue,
    },
    Call {
        dest: Option<String>,
        callee: String,
        args: Vec<IrValue>,
    },
    Load {
        dest: String,
        ptr: String,
    },
    Store {
        ptr: String,
        value: IrValue,
    },
    Alloca {
        dest: String,
        ty: IrType,
    },
}

#[derive(Debug, Clone)]
pub enum IrTerminator {
    Return(Option<IrValue>),
    Branch {
        condition: IrValue,
        true_label: String,
        false_label: String,
    },
    Jump {
        target: String,
    },
}

#[derive(Debug, Clone)]
pub enum IrValue {
    Variable(String),
    Constant(IrConstant),
}

#[derive(Debug, Clone)]
pub enum IrConstant {
    Int(i64),
    Float(f64),
    Bool(bool),
    String(String),
    Unit,
}

#[derive(Debug, Clone)]
pub enum IrType {
    Int,
    Float,
    Bool,
    String,
    Void,
    Pointer(Box<IrType>),
    Function {
        params: Vec<IrType>,
        ret: Box<IrType>,
    },
}

#[derive(Debug, Clone, Copy)]
pub enum IrBinaryOp {
    Add,
    Sub,
    Mul,
    Div,
    Eq,
    Ne,
    Lt,
    Le,
    Gt,
    Ge,
}

#[derive(Debug, Clone, Copy)]
pub enum IrUnaryOp {
    Neg,
    Not,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ir_module_creation() {
        let mut module = IrModule::new("test".to_string());
        assert_eq!(module.name, "test");
        assert_eq!(module.functions.len(), 0);
    }

    #[test]
    fn test_ir_function_creation() {
        let func = IrFunction::new("main".to_string(), vec![], IrType::Void);
        assert_eq!(func.name, "main");
        assert_eq!(func.params.len(), 0);
    }

    #[test]
    fn test_ir_block_creation() {
        let block = IrBlock::new("entry".to_string());
        assert_eq!(block.label, "entry");
        assert_eq!(block.instructions.len(), 0);
    }
}
