package com.example.notification;

import com.example.domain.User;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class NotificationServiceTest {
    @Test
    void testSendNotification() {
        NotificationService service = new NotificationService();
        User user = new User("1", "testuser", "test@example.com");
        
        assertDoesNotThrow(() -> service.sendNotification(user, "Test message"));
    }
}
