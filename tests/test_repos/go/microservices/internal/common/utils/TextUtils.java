package com.greenfuze.microservices.utils;

public class TextUtils {
    public static String formatText(String input) {
        if (input == null || input.isEmpty()) {
            return "";
        }
        // Use ScalaUtils to format the string first, then convert to uppercase
        String formatted = ScalaUtils.formatString(input);
        return formatted.toUpperCase();
    }
}
