mod protocol;
mod handlers;

use protocol::LspServer;
use std::io;

fn main() {
    let mut server = LspServer::new();

    if let Err(e) = server.run() {
        eprintln!("LSP Server error: {}", e);
        std::process::exit(1);
    }
}
