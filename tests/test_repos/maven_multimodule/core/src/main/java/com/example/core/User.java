package com.example.core;

import java.time.LocalDateTime;

/**
 * User entity representing a user in the system.
 */
public class User {
	private Long id;
	private String username;
	private String email;
	private LocalDateTime createdAt;
	private boolean active;

	public User() {
	}

	public User(String username, String email) {
		this.username = username;
		this.email = email;
		this.createdAt = LocalDateTime.now();
		this.active = true;
	}

	// Getters and setters
	public Long getId() {
		return id;
	}

	public void setId(Long id) {
		this.id = id;
	}

	public String getUsername() {
		return username;
	}

	public void setUsername(String username) {
		this.username = username;
	}

	public String getEmail() {
		return email;
	}

	public void setEmail(String email) {
		this.email = email;
	}

	public LocalDateTime getCreatedAt() {
		return createdAt;
	}

	public void setCreatedAt(LocalDateTime createdAt) {
		this.createdAt = createdAt;
	}

	public boolean isActive() {
		return active;
	}

	public void setActive(boolean active) {
		this.active = active;
	}

	@Override
	public String toString() {
		return "User{id=" + id + ", username='" + username + "', email='" + email + "'}";
	}
}
