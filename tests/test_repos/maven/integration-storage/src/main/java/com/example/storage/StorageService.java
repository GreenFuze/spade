package com.example.storage;

import com.example.common.CommonUtils;

/**
 * File storage integration service.
 */
public class StorageService {
    public void saveFile(String filename, byte[] content) {
        String sanitizedFilename = CommonUtils.sanitize(filename);
        if (!sanitizedFilename.isEmpty()) {
            System.out.println("Saving file: " + sanitizedFilename);
        }
    }

    public byte[] loadFile(String filename) {
        return new byte[0];
    }
}
