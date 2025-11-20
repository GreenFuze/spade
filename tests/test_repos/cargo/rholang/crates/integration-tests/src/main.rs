mod test_runner;

use test_runner::TestRunner;

fn main() {
    println!("Running integration tests...");

    let mut runner = TestRunner::new();

    match runner.run_all_tests() {
        Ok(results) => {
            println!("\nTest Results:");
            println!("  Passed: {}", results.passed);
            println!("  Failed: {}", results.failed);
            println!("  Total:  {}", results.total());

            if results.failed > 0 {
                std::process::exit(1);
            }
        }
        Err(e) => {
            eprintln!("Test runner error: {}", e);
            std::process::exit(1);
        }
    }
}
