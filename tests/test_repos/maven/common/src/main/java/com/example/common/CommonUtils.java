package com.example.common;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.google.common.base.Strings;

/**
 * Common utilities shared across modules.
 */
public class CommonUtils {
    private static final Logger logger = LoggerFactory.getLogger(CommonUtils.class);

    public static String sanitize(String input) {
        if (Strings.isNullOrEmpty(input)) {
            return "";
        }
        return input.trim();
    }

    public static void logInfo(String message) {
        logger.info(message);
    }
}
