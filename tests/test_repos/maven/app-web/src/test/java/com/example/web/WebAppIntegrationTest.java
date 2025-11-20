package com.example.web;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WebAppIntegrationTest {
    @Test
    void testWebApplication() {
        WebApplication app = new WebApplication();
        assertNotNull(app);
    }
}
