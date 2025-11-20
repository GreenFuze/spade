package com.example.auth;

import com.example.domain.User;
import com.example.common.CommonUtils;

/**
 * Authentication service.
 */
public class AuthService {
    public boolean authenticate(String username, String password) {
        if (CommonUtils.sanitize(username).isEmpty()) {
            return false;
        }
        return password != null && !password.isEmpty();
    }

    public User getUser(String username) {
        return new User("1", username, username + "@example.com");
    }
}
