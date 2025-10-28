package com.example.core;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

/**
 * Service for managing users.
 */
public class UserService {
	private final List<User> users = new ArrayList<>();
	private Long nextId = 1L;

	/**
	 * Create a new user.
	 */
	public User createUser(String username, String email) {
		User user = new User(username, email);
		user.setId(nextId++);
		users.add(user);
		return user;
	}

	/**
	 * Find user by ID.
	 */
	public Optional<User> findById(Long id) {
		return users.stream()
				.filter(user -> user.getId().equals(id))
				.findFirst();
	}

	/**
	 * Find user by username.
	 */
	public Optional<User> findByUsername(String username) {
		return users.stream()
				.filter(user -> user.getUsername().equals(username))
				.findFirst();
	}

	/**
	 * Get all users.
	 */
	public List<User> getAllUsers() {
		return new ArrayList<>(users);
	}

	/**
	 * Update user.
	 */
	public boolean updateUser(User user) {
		for (int i = 0; i < users.size(); i++) {
			if (users.get(i).getId().equals(user.getId())) {
				users.set(i, user);
				return true;
			}
		}
		return false;
	}

	/**
	 * Delete user by ID.
	 */
	public boolean deleteUser(Long id) {
		return users.removeIf(user -> user.getId().equals(id));
	}
}
