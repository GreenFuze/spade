package com.example.api;

import com.example.core.User;
import com.example.core.UserService;
import java.util.List;
import java.util.Optional;

/**
 * REST controller for user operations.
 */
public class UserController {
    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    /**
     * Create a new user.
     */
    public User createUser(String username, String email) {
        return userService.createUser(username, email);
    }

    /**
     * Get user by ID.
     */
    public Optional<User> getUser(Long id) {
        return userService.findById(id);
    }

    /**
     * Get user by username.
     */
    public Optional<User> getUserByUsername(String username) {
        return userService.findByUsername(username);
    }

    /**
     * Get all users.
     */
    public List<User> getAllUsers() {
        return userService.getAllUsers();
    }

    /**
     * Update user.
     */
    public boolean updateUser(User user) {
        return userService.updateUser(user);
    }

    /**
     * Delete user.
     */
    public boolean deleteUser(Long id) {
        return userService.deleteUser(id);
    }
}
