package com.example.domain;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.example.common.CommonUtils;

/**
 * Task domain model.
 */
public class Task {
    @JsonProperty("id")
    private String id;

    @JsonProperty("title")
    private String title;

    @JsonProperty("description")
    private String description;

    public Task() {
    }

    public Task(String id, String title, String description) {
        this.id = id;
        this.title = CommonUtils.sanitize(title);
        this.description = CommonUtils.sanitize(description);
    }

    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }
}
