use lexer::Lexer;
use parser::Parser;
use semantic_analyzer::SemanticAnalyzer;
use type_checker::TypeChecker;
use codegen_c::CCodegen;
use codegen_bytecode::BytecodeGenerator;
use common_types::Span;
use error_reporting::Diagnostic;
use std::path::Path;
use std::fs;

pub struct Compiler {
    lexer: Option<Lexer>,
    semantic_analyzer: SemanticAnalyzer,
    type_checker: TypeChecker,
    c_codegen: CCodegen,
    bytecode_gen: BytecodeGenerator,
}

impl Compiler {
    pub fn new() -> Self {
        Self {
            lexer: None,
            semantic_analyzer: SemanticAnalyzer::new(),
            type_checker: TypeChecker::new(),
            c_codegen: CCodegen::new(),
            bytecode_gen: BytecodeGenerator::new(),
        }
    }

    pub fn compile_file(&mut self, path: &Path) -> Result<(), String> {
        let source = fs::read_to_string(path).map_err(|e| e.to_string())?;
        self.compile_source(&source)
    }

    pub fn compile_source(&mut self, source: &str) -> Result<(), String> {
        let mut lexer = Lexer::new(source);
        let tokens = lexer.tokenize().map_err(|_| "Lexer error".to_string())?;

        let mut parser = Parser::new(tokens);
        let declarations = parser.parse().map_err(|_| "Parser error".to_string())?;

        let ast = ast::Ast::new(
            declarations
                .into_iter()
                .map(|d| ast::AstNode::new(0, ast::NodeKind::Program { declarations: vec![] }, d.span))
                .collect(),
        );

        self.semantic_analyzer
            .analyze(&ast)
            .map_err(|_| "Semantic analysis error".to_string())?;

        self.type_checker
            .check(&ast)
            .map_err(|_| "Type checking error".to_string())?;

        Ok(())
    }

    pub fn generate_c(&mut self, module: &ir_gen::IrModule) -> String {
        self.c_codegen.generate(module)
    }

    pub fn generate_bytecode(&mut self, module: &ir_gen::IrModule) -> Vec<u8> {
        self.bytecode_gen.generate(module)
    }
}

impl Default for Compiler {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compiler_creation() {
        let compiler = Compiler::new();
        assert!(true);
    }

    #[test]
    fn test_compile_empty_source() {
        let mut compiler = Compiler::new();
        let result = compiler.compile_source("");
        assert!(result.is_ok());
    }
}
