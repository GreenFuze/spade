use std::collections::{HashMap, VecDeque};

pub struct List<T> {
    items: Vec<T>,
}

impl<T> List<T> {
    pub fn new() -> Self {
        Self { items: Vec::new() }
    }

    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            items: Vec::with_capacity(capacity),
        }
    }

    pub fn push(&mut self, item: T) {
        self.items.push(item);
    }

    pub fn pop(&mut self) -> Option<T> {
        self.items.pop()
    }

    pub fn get(&self, index: usize) -> Option<&T> {
        self.items.get(index)
    }

    pub fn set(&mut self, index: usize, item: T) -> Result<(), String> {
        if index >= self.items.len() {
            return Err("Index out of bounds".to_string());
        }
        self.items[index] = item;
        Ok(())
    }

    pub fn len(&self) -> usize {
        self.items.len()
    }

    pub fn is_empty(&self) -> bool {
        self.items.is_empty()
    }

    pub fn clear(&mut self) {
        self.items.clear();
    }
}

impl<T> Default for List<T> {
    fn default() -> Self {
        Self::new()
    }
}

pub struct Map<K, V> {
    data: HashMap<K, V>,
}

impl<K: std::hash::Hash + Eq, V> Map<K, V> {
    pub fn new() -> Self {
        Self {
            data: HashMap::new(),
        }
    }

    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        self.data.insert(key, value)
    }

    pub fn get(&self, key: &K) -> Option<&V> {
        self.data.get(key)
    }

    pub fn remove(&mut self, key: &K) -> Option<V> {
        self.data.remove(key)
    }

    pub fn contains_key(&self, key: &K) -> bool {
        self.data.contains_key(key)
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

impl<K: std::hash::Hash + Eq, V> Default for Map<K, V> {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_list() {
        let mut list = List::new();
        list.push(1);
        list.push(2);
        assert_eq!(list.len(), 2);
        assert_eq!(list.pop(), Some(2));
    }

    #[test]
    fn test_map() {
        let mut map = Map::new();
        map.insert("key", "value");
        assert_eq!(map.get(&"key"), Some(&"value"));
    }
}
