mod compile;

use compile::Compiler;
use std::path::PathBuf;

fn main() {
    let args: Vec<String> = std::env::args().collect();

    if args.len() < 2 {
        eprintln!("Usage: rholang-cli <input-file>");
        std::process::exit(1);
    }

    let input_file = PathBuf::from(&args[1]);

    let mut compiler = Compiler::new();

    match compiler.compile_file(&input_file) {
        Ok(_) => {
            println!("Compilation successful");
        }
        Err(e) => {
            eprintln!("Compilation error: {}", e);
            std::process::exit(1);
        }
    }
}
