package com.example.notification;

import com.example.domain.User;
import com.example.common.CommonUtils;

/**
 * Notification service.
 */
public class NotificationService {
    public void sendNotification(User user, String message) {
        String sanitizedMessage = CommonUtils.sanitize(message);
        if (!sanitizedMessage.isEmpty()) {
            // Simulate sending notification
            System.out.println("Notification to " + user.getEmail() + ": " + sanitizedMessage);
        }
    }
}
