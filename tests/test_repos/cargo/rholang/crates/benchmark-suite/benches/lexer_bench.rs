use lexer::Lexer;

fn bench_lexer_small() {
    let source = "let x = 42;";
    let mut lexer = Lexer::new(source);
    let _ = lexer.tokenize();
}

fn bench_lexer_medium() {
    let source = "let x = 42; let y = x + 10; ".repeat(50);
    let mut lexer = Lexer::new(&source);
    let _ = lexer.tokenize();
}

fn bench_lexer_large() {
    let source = "let x = 42; ".repeat(1000);
    let mut lexer = Lexer::new(&source);
    let _ = lexer.tokenize();
}

fn bench_lexer_keywords() {
    let source = "let fn if else while for return ";
    let mut lexer = Lexer::new(source);
    let _ = lexer.tokenize();
}

fn bench_lexer_operators() {
    let source = "+ - * / == != < > <= >= && || ! ";
    let mut lexer = Lexer::new(source);
    let _ = lexer.tokenize();
}

fn bench_lexer_numbers() {
    let source = "0 1 42 123 999 1234567890 ";
    let mut lexer = Lexer::new(source);
    let _ = lexer.tokenize();
}

fn bench_lexer_strings() {
    let source = r#""hello" "world" "test string" "another test" "#;
    let mut lexer = Lexer::new(source);
    let _ = lexer.tokenize();
}

fn bench_lexer_identifiers() {
    let source = "foo bar baz variable function_name my_var ";
    let mut lexer = Lexer::new(source);
    let _ = lexer.tokenize();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bench_lexer_small() {
        bench_lexer_small();
    }

    #[test]
    fn test_bench_lexer_medium() {
        bench_lexer_medium();
    }

    #[test]
    fn test_bench_lexer_large() {
        bench_lexer_large();
    }
}
