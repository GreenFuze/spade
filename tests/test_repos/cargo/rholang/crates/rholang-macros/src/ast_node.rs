//! AST node macro utilities

use syn::{Data, DeriveInput, Fields};

pub fn impl_ast_node(input: &DeriveInput) -> proc_macro2::TokenStream {
    let name = &input.ident;

    match &input.data {
        Data::Struct(data_struct) => {
            match &data_struct.fields {
                Fields::Named(_) => {
                    quote::quote! {
                        impl AstNode for #name {
                            fn node_type(&self) -> &'static str {
                                stringify!(#name)
                            }
                        }
                    }
                }
                _ => panic!("Only named fields supported"),
            }
        }
        _ => panic!("Only structs supported"),
    }
}
