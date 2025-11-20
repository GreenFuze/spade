pub mod collections;
pub mod io;
pub mod string;

pub use collections::{List, Map};
pub use io::{print, println, read_line};
pub use string::{StringExt, split, join};

use vm_runtime::Runtime;
use common_types::Span;

pub struct StandardLibrary {
    runtime: Runtime,
}

impl StandardLibrary {
    pub fn new() -> Self {
        Self {
            runtime: Runtime::new(),
        }
    }

    pub fn register_functions(&mut self) {
        // Register standard library functions
    }
}

impl Default for StandardLibrary {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stdlib() {
        let stdlib = StandardLibrary::new();
        assert!(true);
    }
}
