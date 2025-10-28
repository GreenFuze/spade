use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

/// Derive macro for adding debug information to structs.
#[proc_macro_derive(DebugInfo)]
pub fn derive_debug_info(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;

    let expanded = quote! {
        impl #name {
            pub fn debug_info(&self) -> String {
                format!("Debug info for {}", stringify!(#name))
            }
        }
    };

    TokenStream::from(expanded)
}

/// Attribute macro for adding version information.
#[proc_macro_attribute]
pub fn version(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as DeriveInput);
    let name = &input.ident;

    let expanded = quote! {
        #input
        
        impl #name {
            pub const VERSION: &'static str = "1.0.0";
        }
    };

    TokenStream::from(expanded)
}
