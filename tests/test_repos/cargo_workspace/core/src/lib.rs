use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// User entity representing a user in the system.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: u64,
    pub username: String,
    pub email: String,
    pub active: bool,
}

impl User {
    pub fn new(username: String, email: String) -> Self {
        Self {
            id: 0, // Will be set by the service
            username,
            email,
            active: true,
        }
    }
}

/// Service for managing users.
pub struct UserService {
    users: HashMap<u64, User>,
    next_id: u64,
}

impl UserService {
    pub fn new() -> Self {
        Self {
            users: HashMap::new(),
            next_id: 1,
        }
    }

    /// Create a new user.
    pub fn create_user(&mut self, username: String, email: String) -> User {
        let mut user = User::new(username, email);
        user.id = self.next_id;
        self.next_id += 1;
        self.users.insert(user.id, user.clone());
        user
    }

    /// Find user by ID.
    pub fn find_by_id(&self, id: u64) -> Option<&User> {
        self.users.get(&id)
    }

    /// Find user by username.
    pub fn find_by_username(&self, username: &str) -> Option<&User> {
        self.users.values().find(|user| user.username == username)
    }

    /// Get all users.
    pub fn get_all_users(&self) -> Vec<&User> {
        self.users.values().collect()
    }

    /// Update user.
    pub fn update_user(&mut self, user: User) -> bool {
        if self.users.contains_key(&user.id) {
            self.users.insert(user.id, user);
            true
        } else {
            false
        }
    }

    /// Delete user by ID.
    pub fn delete_user(&mut self, id: u64) -> bool {
        self.users.remove(&id).is_some()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_create_user() {
        let mut service = UserService::new();
        let user = service.create_user("john_doe".to_string(), "john@example.com".to_string());
        
        assert_eq!(user.username, "john_doe");
        assert_eq!(user.email, "john@example.com");
        assert!(user.active);
        assert_eq!(user.id, 1);
    }

    #[test]
    fn test_find_by_id() {
        let mut service = UserService::new();
        let user = service.create_user("jane_doe".to_string(), "jane@example.com".to_string());
        let user_id = user.id;

        assert!(service.find_by_id(user_id).is_some());
        assert!(service.find_by_id(999).is_none());
    }

    #[test]
    fn test_find_by_username() {
        let mut service = UserService::new();
        service.create_user("alice".to_string(), "alice@example.com".to_string());

        assert!(service.find_by_username("alice").is_some());
        assert!(service.find_by_username("bob").is_none());
    }
}
