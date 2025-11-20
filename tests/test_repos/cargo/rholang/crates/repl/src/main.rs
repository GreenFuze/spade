mod eval;

use eval::Evaluator;
use std::io::{self, Write};

fn main() {
    println!("RhoLang REPL v0.1.0");
    println!("Type 'exit' to quit");

    let mut evaluator = Evaluator::new();
    let stdin = io::stdin();
    let mut stdout = io::stdout();

    loop {
        print!("> ");
        stdout.flush().unwrap();

        let mut input = String::new();
        if stdin.read_line(&mut input).is_err() {
            break;
        }

        let input = input.trim();

        if input == "exit" || input == "quit" {
            break;
        }

        if input.is_empty() {
            continue;
        }

        match evaluator.eval(input) {
            Ok(result) => {
                println!("{}", result);
            }
            Err(e) => {
                eprintln!("Error: {}", e);
            }
        }
    }

    println!("Goodbye!");
}
