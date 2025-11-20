package com.example.domain;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DomainModelTest {
    @Test
    void testTask() {
        Task task = new Task("1", "Test Task", "Description");
        assertEquals("1", task.getId());
        assertEquals("Test Task", task.getTitle());
    }

    @Test
    void testUser() {
        User user = new User("1", "testuser", "test@example.com");
        assertEquals("1", user.getId());
        assertEquals("testuser", user.getUsername());
    }
}
