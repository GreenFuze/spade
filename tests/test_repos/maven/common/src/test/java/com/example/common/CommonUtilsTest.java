package com.example.common;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CommonUtilsTest {
    @Test
    void testSanitize() {
        assertEquals("test", CommonUtils.sanitize("  test  "));
        assertEquals("", CommonUtils.sanitize(null));
    }

    @Test
    void testLogInfo() {
        assertDoesNotThrow(() -> CommonUtils.logInfo("Test message"));
    }
}
