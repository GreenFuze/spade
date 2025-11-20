// Build script for compiling C code in the FFI bridge
// Demonstrates Cargo build-time code compilation

fn main() {
    // Compile native.c using the cc crate
    cc::Build::new()
        .file("src/native.c")
        .include("include")
        .warnings(true)
        .extra_warnings(true)
        .compile("rholang_native");

    // Tell cargo to rerun this build script if native.c or the header changes
    println!("cargo:rerun-if-changed=src/native.c");
    println!("cargo:rerun-if-changed=include/rholang.h");

    // Link against the compiled C library
    println!("cargo:rustc-link-lib=static=rholang_native");

    // Generate Rust bindings from C header (optional, but demonstrates bindgen)
    // In a real project, you might use bindgen here:
    // let bindings = bindgen::Builder::default()
    //     .header("include/rholang.h")
    //     .generate()
    //     .expect("Unable to generate bindings");
    // bindings.write_to_file("src/bindings.rs").expect("Couldn't write bindings!");

    println!("cargo:info=FFI bridge C code compiled successfully");
}
