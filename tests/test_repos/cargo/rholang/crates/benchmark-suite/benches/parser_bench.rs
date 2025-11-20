use lexer::Lexer;
use parser::Parser;

fn bench_parser_simple_expr() {
    let source = "let x = 42;";
    let mut lexer = Lexer::new(source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

fn bench_parser_binary_expr() {
    let source = "let x = 1 + 2 * 3 - 4 / 5;";
    let mut lexer = Lexer::new(source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

fn bench_parser_function_decl() {
    let source = r#"
        fn add(a, b) {
            return a + b;
        }
    "#;
    let mut lexer = Lexer::new(source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

fn bench_parser_if_statement() {
    let source = r#"
        if x > 0 {
            return 1;
        } else {
            return 0;
        }
    "#;
    let mut lexer = Lexer::new(source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

fn bench_parser_while_loop() {
    let source = r#"
        while x < 10 {
            x = x + 1;
        }
    "#;
    let mut lexer = Lexer::new(source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

fn bench_parser_nested_expressions() {
    let source = "let x = (1 + (2 * (3 - (4 / 5))));";
    let mut lexer = Lexer::new(source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

fn bench_parser_multiple_statements() {
    let source = "let x = 1; let y = 2; let z = 3; ".repeat(10);
    let mut lexer = Lexer::new(&source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

fn bench_parser_complex_program() {
    let source = r#"
        fn factorial(n) {
            if n <= 1 {
                return 1;
            } else {
                return n * factorial(n - 1);
            }
        }

        fn main() {
            let result = factorial(10);
            return result;
        }
    "#;
    let mut lexer = Lexer::new(source);
    if let Ok(tokens) = lexer.tokenize() {
        let mut parser = Parser::new(tokens);
        let _ = parser.parse();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bench_parser_simple() {
        bench_parser_simple_expr();
    }

    #[test]
    fn test_bench_parser_binary() {
        bench_parser_binary_expr();
    }

    #[test]
    fn test_bench_parser_function() {
        bench_parser_function_decl();
    }
}
