package com.example.auth;

import com.example.domain.User;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import static org.junit.jupiter.api.Assertions.*;

class AuthServiceTest {
    @Test
    void testAuthenticate() {
        AuthService service = new AuthService();
        assertTrue(service.authenticate("user", "pass"));
        assertFalse(service.authenticate("", "pass"));
    }

    @Test
    void testGetUser() {
        AuthService service = new AuthService();
        User user = service.getUser("testuser");
        assertNotNull(user);
        assertEquals("testuser", user.getUsername());
    }
}
