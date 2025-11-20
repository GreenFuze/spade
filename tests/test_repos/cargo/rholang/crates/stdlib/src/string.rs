pub trait StringExt {
    fn reverse(&self) -> String;
    fn to_uppercase_custom(&self) -> String;
    fn to_lowercase_custom(&self) -> String;
    fn trim_custom(&self) -> String;
}

impl StringExt for str {
    fn reverse(&self) -> String {
        self.chars().rev().collect()
    }

    fn to_uppercase_custom(&self) -> String {
        self.to_uppercase()
    }

    fn to_lowercase_custom(&self) -> String {
        self.to_lowercase()
    }

    fn trim_custom(&self) -> String {
        self.trim().to_string()
    }
}

pub fn split(s: &str, delimiter: &str) -> Vec<String> {
    s.split(delimiter).map(|s| s.to_string()).collect()
}

pub fn join(parts: &[String], separator: &str) -> String {
    parts.join(separator)
}

pub fn concat(strings: &[&str]) -> String {
    strings.concat()
}

pub fn replace(s: &str, from: &str, to: &str) -> String {
    s.replace(from, to)
}

pub fn starts_with(s: &str, prefix: &str) -> bool {
    s.starts_with(prefix)
}

pub fn ends_with(s: &str, suffix: &str) -> bool {
    s.ends_with(suffix)
}

pub fn contains(s: &str, needle: &str) -> bool {
    s.contains(needle)
}

pub fn substring(s: &str, start: usize, end: usize) -> String {
    s.chars().skip(start).take(end - start).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reverse() {
        assert_eq!("hello".reverse(), "olleh");
    }

    #[test]
    fn test_split() {
        let parts = split("a,b,c", ",");
        assert_eq!(parts, vec!["a", "b", "c"]);
    }

    #[test]
    fn test_join() {
        let parts = vec!["a".to_string(), "b".to_string(), "c".to_string()];
        assert_eq!(join(&parts, ","), "a,b,c");
    }

    #[test]
    fn test_contains() {
        assert!(contains("hello world", "world"));
        assert!(!contains("hello", "world"));
    }
}
