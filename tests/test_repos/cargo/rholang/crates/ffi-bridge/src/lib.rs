use vm_runtime::{Runtime, VMError};
use common_types::Span;
use std::ffi::{CStr, CString};
use std::os::raw::{c_char, c_int, c_void};

// External C functions from native.c (Rust -> C)
extern "C" {
    fn rholang_native_init() -> c_int;
    fn rholang_native_cleanup();
    fn rholang_native_alloc(size: usize) -> *mut c_void;
    fn rholang_native_free(ptr: *mut c_void);
    fn rholang_native_getenv(name: *const c_char) -> *const c_char;
    fn rholang_native_file_exists(path: *const c_char) -> c_int;
}

pub struct FFIBridge {
    runtime: Runtime,
    initialized: bool,
}

impl FFIBridge {
    pub fn new() -> Self {
        // Call C initialization (Rust -> C)
        let init_result = unsafe { rholang_native_init() };

        Self {
            runtime: Runtime::new(),
            initialized: init_result == 0,
        }
    }

    /// Call native C function to check if file exists
    pub fn native_file_exists(&self, path: &str) -> bool {
        let c_path = CString::new(path).unwrap();
        unsafe {
            rholang_native_file_exists(c_path.as_ptr()) != 0
        }
    }

    /// Get environment variable via native C function
    pub fn native_getenv(&self, name: &str) -> Option<String> {
        let c_name = CString::new(name).unwrap();
        unsafe {
            let result = rholang_native_getenv(c_name.as_ptr());
            if result.is_null() {
                None
            } else {
                Some(CStr::from_ptr(result).to_string_lossy().into_owned())
            }
        }
    }

    pub fn execute_bytecode(&mut self, bytecode: &[u8]) -> Result<i64, String> {
        match self.runtime.execute(bytecode) {
            Ok(Some(codegen_bytecode::instruction::Value::Int(i))) => Ok(i),
            Ok(Some(_)) => Ok(0),
            Ok(None) => Ok(0),
            Err(_) => Err("VM error".to_string()),
        }
    }
}

impl Default for FFIBridge {
    fn default() -> Self {
        Self::new()
    }
}

impl Drop for FFIBridge {
    fn drop(&mut self) {
        if self.initialized {
            // Call C cleanup (Rust -> C)
            unsafe {
                rholang_native_cleanup();
            }
        }
    }
}

#[no_mangle]
pub extern "C" fn rholang_create() -> *mut FFIBridge {
    Box::into_raw(Box::new(FFIBridge::new()))
}

#[no_mangle]
pub extern "C" fn rholang_destroy(bridge: *mut FFIBridge) {
    if !bridge.is_null() {
        unsafe {
            let _ = Box::from_raw(bridge);
        }
    }
}

#[no_mangle]
pub extern "C" fn rholang_execute(
    bridge: *mut FFIBridge,
    bytecode: *const u8,
    len: usize,
) -> c_int {
    if bridge.is_null() || bytecode.is_null() {
        return -1;
    }

    unsafe {
        let bridge_ref = &mut *bridge;
        let bytecode_slice = std::slice::from_raw_parts(bytecode, len);

        match bridge_ref.execute_bytecode(bytecode_slice) {
            Ok(result) => result as c_int,
            Err(_) => -1,
        }
    }
}

// Additional C-callable exports (C -> Rust)
// These implement the functions declared in rholang.h

#[no_mangle]
pub extern "C" fn rholang_runtime_init() -> c_int {
    // Initialize global runtime
    0 // Success
}

#[no_mangle]
pub extern "C" fn rholang_execute_code(source_code: *const c_char, len: usize) -> c_int {
    if source_code.is_null() {
        return -1;
    }

    unsafe {
        let code_slice = std::slice::from_raw_parts(source_code as *const u8, len);
        // In a real implementation, would compile and execute the code
        // For now, just return success
        0
    }
}

#[no_mangle]
pub extern "C" fn rholang_runtime_shutdown() {
    // Shutdown global runtime
}

#[no_mangle]
pub extern "C" fn rholang_get_version() -> *const c_char {
    static VERSION: &[u8] = b"RhoLang 0.1.0\0";
    VERSION.as_ptr() as *const c_char
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ffi_bridge_creation() {
        let bridge = FFIBridge::new();
        assert!(bridge.initialized);
    }

    #[test]
    fn test_ffi_c_interface() {
        let bridge = rholang_create();
        assert!(!bridge.is_null());
        rholang_destroy(bridge);
    }

    #[test]
    fn test_native_file_exists() {
        let bridge = FFIBridge::new();
        // This will call the C function
        let exists = bridge.native_file_exists("/nonexistent/path");
        assert!(!exists);
    }

    #[test]
    fn test_version_export() {
        unsafe {
            let version_ptr = rholang_get_version();
            assert!(!version_ptr.is_null());
            let version = CStr::from_ptr(version_ptr).to_str().unwrap();
            assert!(version.contains("RhoLang"));
        }
    }
}
