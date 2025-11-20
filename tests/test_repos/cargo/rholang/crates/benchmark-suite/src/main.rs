use std::time::{Duration, Instant};

fn main() {
    println!("RhoLang Benchmark Suite");
    println!("=======================\n");

    run_lexer_benchmarks();
    run_parser_benchmarks();
    run_semantic_benchmarks();
    run_vm_benchmarks();
}

fn run_lexer_benchmarks() {
    println!("Lexer Benchmarks:");

    benchmark("Lexer: Small input (100 tokens)", || {
        let source = "let x = 42; let y = x + 10; return y;";
        let mut lexer = lexer::Lexer::new(source);
        let _ = lexer.tokenize();
    });

    benchmark("Lexer: Medium input (1000 tokens)", || {
        let source = "let x = 42; ".repeat(100);
        let mut lexer = lexer::Lexer::new(&source);
        let _ = lexer.tokenize();
    });

    println!();
}

fn run_parser_benchmarks() {
    println!("Parser Benchmarks:");

    benchmark("Parser: Simple expression", || {
        let source = "let x = 42;";
        let mut lexer = lexer::Lexer::new(source);
        if let Ok(tokens) = lexer.tokenize() {
            let mut parser = parser::Parser::new(tokens);
            let _ = parser.parse();
        }
    });

    println!();
}

fn run_semantic_benchmarks() {
    println!("Semantic Analysis Benchmarks:");

    benchmark("Semantic: Empty AST", || {
        let mut analyzer = semantic_analyzer::SemanticAnalyzer::new();
        let ast = ast::Ast::empty();
        let _ = analyzer.analyze(&ast);
    });

    println!();
}

fn run_vm_benchmarks() {
    println!("VM Benchmarks:");

    benchmark("VM: Halt instruction", || {
        let mut runtime = vm_runtime::Runtime::new();
        let bytecode = vec![0xFF]; // Halt
        let _ = runtime.execute(&bytecode);
    });

    println!();
}

fn benchmark<F: FnMut()>(name: &str, mut f: F) {
    const ITERATIONS: usize = 1000;

    let start = Instant::now();
    for _ in 0..ITERATIONS {
        f();
    }
    let duration = start.elapsed();

    let avg_time = duration / ITERATIONS as u32;

    println!(
        "  {} - {} iterations in {:?} (avg: {:?})",
        name, ITERATIONS, duration, avg_time
    );
}
