use codegen_bytecode::instruction::Value;

pub struct Stack {
    data: Vec<Value>,
    max_size: usize,
}

impl Stack {
    pub fn new(max_size: usize) -> Self {
        Self {
            data: Vec::with_capacity(max_size),
            max_size,
        }
    }

    pub fn push(&mut self, value: Value) -> Result<(), String> {
        if self.data.len() >= self.max_size {
            return Err("Stack overflow".to_string());
        }
        self.data.push(value);
        Ok(())
    }

    pub fn pop(&mut self) -> Result<Value, String> {
        self.data.pop().ok_or_else(|| "Stack underflow".to_string())
    }

    pub fn peek(&self) -> Option<&Value> {
        self.data.last()
    }

    pub fn get(&self, index: usize) -> Option<&Value> {
        self.data.get(index)
    }

    pub fn set(&mut self, index: usize, value: Value) -> Result<(), String> {
        if index >= self.data.len() {
            return Err("Stack index out of bounds".to_string());
        }
        self.data[index] = value;
        Ok(())
    }

    pub fn len(&self) -> usize {
        self.data.len()
    }

    pub fn is_empty(&self) -> bool {
        self.data.is_empty()
    }

    pub fn clear(&mut self) {
        self.data.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stack_push_pop() {
        let mut stack = Stack::new(10);
        assert!(stack.push(Value::Int(42)).is_ok());
        assert_eq!(stack.len(), 1);

        let value = stack.pop().unwrap();
        match value {
            Value::Int(i) => assert_eq!(i, 42),
            _ => panic!("Wrong value type"),
        }
    }

    #[test]
    fn test_stack_overflow() {
        let mut stack = Stack::new(1);
        assert!(stack.push(Value::Int(1)).is_ok());
        assert!(stack.push(Value::Int(2)).is_err());
    }

    #[test]
    fn test_stack_underflow() {
        let mut stack = Stack::new(10);
        assert!(stack.pop().is_err());
    }
}
