package com.example.task;

import com.example.domain.Task;
import com.example.persistence.TaskRepository;
import com.example.common.CommonUtils;

/**
 * Task management service.
 */
public class TaskService {
    private TaskRepository repository;

    public TaskService(TaskRepository repository) {
        this.repository = repository;
    }

    public Task createTask(String title, String description) {
        String id = CommonUtils.sanitize(title).toLowerCase().replace(" ", "-");
        Task task = new Task(id, title, description);
        repository.save(task);
        return task;
    }

    public Task getTask(String id) {
        return repository.findById(id);
    }
}
