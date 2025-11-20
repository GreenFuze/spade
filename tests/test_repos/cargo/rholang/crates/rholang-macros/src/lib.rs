//! Procedural macros for the RhoLang compiler.
//!
//! This crate provides derive macros for AST node generation and visitor patterns.

extern crate proc_macro;

use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

pub mod ast_node;
pub mod visitor;

/// Derive macro for AST nodes with automatic visitor support
#[proc_macro_derive(AstNode)]
pub fn derive_ast_node(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;

    let expanded = quote! {
        impl #name {
            pub fn accept<V: Visitor>(&self, visitor: &mut V) {
                visitor.visit(self);
            }
        }
    };

    TokenStream::from(expanded)
}

/// Derive macro for visitor pattern implementation
#[proc_macro_derive(Visitor)]
pub fn derive_visitor(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;

    let expanded = quote! {
        impl Visitor for #name {
            fn visit<N>(&mut self, node: &N) {
                // Default implementation
            }
        }
    };

    TokenStream::from(expanded)
}
