package com.example.email;

import com.example.common.CommonUtils;

/**
 * Email integration service.
 */
public class EmailService {
    public void sendEmail(String to, String subject, String body) {
        String sanitizedTo = CommonUtils.sanitize(to);
        if (!sanitizedTo.isEmpty()) {
            System.out.println("Sending email to: " + sanitizedTo);
        }
    }
}
