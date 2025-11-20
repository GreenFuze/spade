//! Visitor pattern macro utilities

use syn::DeriveInput;

pub fn impl_visitor(input: &DeriveInput) -> proc_macro2::TokenStream {
    let name = &input.ident;

    quote::quote! {
        trait Visitor {
            fn visit<N>(&mut self, node: &N);
        }

        impl Visitor for #name {
            fn visit<N>(&mut self, node: &N) {
                // Custom visitor implementation
            }
        }
    }
}
