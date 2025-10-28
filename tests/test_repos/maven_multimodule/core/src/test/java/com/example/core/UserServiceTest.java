package com.example.core;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for UserService.
 */
class UserServiceTest {
	private UserService userService;

	@BeforeEach
	void setUp() {
		userService = new UserService();
	}

	@Test
	void testCreateUser() {
		User user = userService.createUser("john_doe", "john@example.com");

		assertNotNull(user);
		assertNotNull(user.getId());
		assertEquals("john_doe", user.getUsername());
		assertEquals("john@example.com", user.getEmail());
		assertTrue(user.isActive());
		assertNotNull(user.getCreatedAt());
	}

	@Test
	void testFindById() {
		User user = userService.createUser("jane_doe", "jane@example.com");
		Long userId = user.getId();

		assertTrue(userService.findById(userId).isPresent());
		assertEquals(user, userService.findById(userId).get());
		assertFalse(userService.findById(999L).isPresent());
	}

	@Test
	void testFindByUsername() {
		userService.createUser("alice", "alice@example.com");

		assertTrue(userService.findByUsername("alice").isPresent());
		assertFalse(userService.findByUsername("bob").isPresent());
	}

	@Test
	void testGetAllUsers() {
		assertEquals(0, userService.getAllUsers().size());

		userService.createUser("user1", "user1@example.com");
		userService.createUser("user2", "user2@example.com");

		assertEquals(2, userService.getAllUsers().size());
	}

	@Test
	void testUpdateUser() {
		User user = userService.createUser("test_user", "test@example.com");
		user.setEmail("updated@example.com");

		assertTrue(userService.updateUser(user));
		assertEquals("updated@example.com",
				userService.findById(user.getId()).get().getEmail());
	}

	@Test
	void testDeleteUser() {
		User user = userService.createUser("delete_me", "delete@example.com");
		Long userId = user.getId();

		assertTrue(userService.deleteUser(userId));
		assertFalse(userService.findById(userId).isPresent());
		assertFalse(userService.deleteUser(999L));
	}
}
