use codegen_bytecode::instruction::Value;
use std::collections::HashMap;

pub type HeapAddress = usize;

pub struct Heap {
    memory: HashMap<HeapAddress, Value>,
    next_addr: HeapAddress,
}

impl Heap {
    pub fn new() -> Self {
        Self {
            memory: HashMap::new(),
            next_addr: 0,
        }
    }

    pub fn allocate(&mut self, value: Value) -> HeapAddress {
        let addr = self.next_addr;
        self.memory.insert(addr, value);
        self.next_addr += 1;
        addr
    }

    pub fn read(&self, addr: HeapAddress) -> Option<&Value> {
        self.memory.get(&addr)
    }

    pub fn write(&mut self, addr: HeapAddress, value: Value) -> Result<(), String> {
        if !self.memory.contains_key(&addr) {
            return Err(format!("Invalid heap address: {}", addr));
        }
        self.memory.insert(addr, value);
        Ok(())
    }

    pub fn free(&mut self, addr: HeapAddress) -> Result<(), String> {
        self.memory
            .remove(&addr)
            .ok_or_else(|| format!("Invalid heap address: {}", addr))?;
        Ok(())
    }

    pub fn size(&self) -> usize {
        self.memory.len()
    }

    pub fn clear(&mut self) {
        self.memory.clear();
        self.next_addr = 0;
    }
}

impl Default for Heap {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_heap_allocate() {
        let mut heap = Heap::new();
        let addr = heap.allocate(Value::Int(42));
        assert_eq!(addr, 0);

        let value = heap.read(addr).unwrap();
        match value {
            Value::Int(i) => assert_eq!(*i, 42),
            _ => panic!("Wrong value type"),
        }
    }

    #[test]
    fn test_heap_write() {
        let mut heap = Heap::new();
        let addr = heap.allocate(Value::Int(10));

        assert!(heap.write(addr, Value::Int(20)).is_ok());

        let value = heap.read(addr).unwrap();
        match value {
            Value::Int(i) => assert_eq!(*i, 20),
            _ => panic!("Wrong value type"),
        }
    }

    #[test]
    fn test_heap_free() {
        let mut heap = Heap::new();
        let addr = heap.allocate(Value::Int(42));
        assert_eq!(heap.size(), 1);

        assert!(heap.free(addr).is_ok());
        assert_eq!(heap.size(), 0);
    }
}
