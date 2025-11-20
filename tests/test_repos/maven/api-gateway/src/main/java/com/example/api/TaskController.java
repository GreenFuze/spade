package com.example.api;

import com.example.task.TaskService;
import com.example.auth.AuthService;
import com.example.notification.NotificationService;
import com.example.domain.Task;
import org.springframework.web.bind.annotation.*;

/**
 * REST API gateway controller.
 */
@RestController
@RequestMapping("/api")
public class TaskController {
    private TaskService taskService;
    private AuthService authService;
    private NotificationService notificationService;

    public TaskController(TaskService taskService, AuthService authService, NotificationService notificationService) {
        this.taskService = taskService;
        this.authService = authService;
        this.notificationService = notificationService;
    }

    @PostMapping("/tasks")
    public Task createTask(@RequestBody Task task) {
        return taskService.createTask(task.getTitle(), task.getDescription());
    }

    @GetMapping("/tasks/{id}")
    public Task getTask(@PathVariable String id) {
        return taskService.getTask(id);
    }
}
