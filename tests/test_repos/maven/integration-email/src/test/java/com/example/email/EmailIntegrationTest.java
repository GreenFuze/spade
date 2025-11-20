package com.example.email;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class EmailIntegrationTest {
    @Test
    void testSendEmail() {
        EmailService service = new EmailService();
        assertDoesNotThrow(() -> service.sendEmail("test@example.com", "Subject", "Body"));
    }
}
