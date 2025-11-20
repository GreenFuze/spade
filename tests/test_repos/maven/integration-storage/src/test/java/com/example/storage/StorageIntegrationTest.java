package com.example.storage;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class StorageIntegrationTest {
    @Test
    void testSaveFile() {
        StorageService service = new StorageService();
        assertDoesNotThrow(() -> service.saveFile("test.txt", new byte[10]));
    }

    @Test
    void testLoadFile() {
        StorageService service = new StorageService();
        byte[] result = service.loadFile("test.txt");
        assertNotNull(result);
    }
}
