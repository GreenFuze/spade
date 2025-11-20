package com.example.api;

import com.example.task.TaskService;
import com.example.auth.AuthService;
import com.example.notification.NotificationService;
import com.example.domain.Task;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import static org.junit.jupiter.api.Assertions.*;

class ApiGatewayTest {
    @Test
    void testTaskController() {
        TaskService taskService = Mockito.mock(TaskService.class);
        AuthService authService = Mockito.mock(AuthService.class);
        NotificationService notificationService = Mockito.mock(NotificationService.class);
        
        TaskController controller = new TaskController(taskService, authService, notificationService);
        assertNotNull(controller);
    }
}
