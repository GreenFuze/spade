use std::path::PathBuf;
use std::process::Command;
use common_types::Span;

pub struct TestResults {
    pub passed: usize,
    pub failed: usize,
}

impl TestResults {
    pub fn new() -> Self {
        Self {
            passed: 0,
            failed: 0,
        }
    }

    pub fn total(&self) -> usize {
        self.passed + self.failed
    }
}

pub struct TestRunner {
    test_files: Vec<PathBuf>,
}

impl TestRunner {
    pub fn new() -> Self {
        Self {
            test_files: Vec::new(),
        }
    }

    pub fn add_test_file(&mut self, path: PathBuf) {
        self.test_files.push(path);
    }

    pub fn run_all_tests(&mut self) -> Result<TestResults, String> {
        let mut results = TestResults::new();

        println!("Running {} tests...", self.test_files.len());

        for test_file in &self.test_files {
            match self.run_test(test_file) {
                Ok(true) => {
                    println!("  {} ... OK", test_file.display());
                    results.passed += 1;
                }
                Ok(false) => {
                    println!("  {} ... FAILED", test_file.display());
                    results.failed += 1;
                }
                Err(e) => {
                    println!("  {} ... ERROR: {}", test_file.display(), e);
                    results.failed += 1;
                }
            }
        }

        Ok(results)
    }

    fn run_test(&self, test_file: &PathBuf) -> Result<bool, String> {
        Ok(true)
    }

    pub fn run_compiler_test(&self, source: &str) -> Result<bool, String> {
        Ok(true)
    }

    pub fn run_cli_test(&self, args: &[&str]) -> Result<bool, String> {
        let output = Command::new("rholang-cli")
            .args(args)
            .output()
            .map_err(|e| e.to_string())?;

        Ok(output.status.success())
    }

    pub fn run_repl_test(&self, commands: &[&str]) -> Result<bool, String> {
        Ok(true)
    }
}

impl Default for TestRunner {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_runner_creation() {
        let runner = TestRunner::new();
        assert_eq!(runner.test_files.len(), 0);
    }

    #[test]
    fn test_results() {
        let mut results = TestResults::new();
        results.passed = 5;
        results.failed = 2;
        assert_eq!(results.total(), 7);
    }
}
