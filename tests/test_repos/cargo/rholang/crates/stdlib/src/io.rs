use std::io::{self, Write, BufRead};

pub fn print(s: &str) {
    print!("{}", s);
    io::stdout().flush().ok();
}

pub fn println(s: &str) {
    println!("{}", s);
}

pub fn read_line() -> Result<String, io::Error> {
    let stdin = io::stdin();
    let mut line = String::new();
    stdin.lock().read_line(&mut line)?;
    Ok(line.trim().to_string())
}

pub struct File {
    path: String,
}

impl File {
    pub fn open(path: &str) -> Result<Self, io::Error> {
        Ok(Self {
            path: path.to_string(),
        })
    }

    pub fn read(&self) -> Result<String, io::Error> {
        std::fs::read_to_string(&self.path)
    }

    pub fn write(&self, content: &str) -> Result<(), io::Error> {
        std::fs::write(&self.path, content)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_print() {
        print("test");
        println("test");
        assert!(true);
    }
}
