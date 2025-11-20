package com.example.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.example.common.CommonUtils;

/**
 * User domain model.
 */
public class User {
    @JsonProperty("id")
    private String id;

    @JsonProperty("username")
    private String username;

    @JsonProperty("email")
    private String email;

    public User() {
    }

    public User(String id, String username, String email) {
        this.id = id;
        this.username = CommonUtils.sanitize(username);
        this.email = CommonUtils.sanitize(email);
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }
}
