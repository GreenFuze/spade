package com.example.task;

import com.example.domain.Task;
import com.example.persistence.TaskRepository;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import static org.junit.jupiter.api.Assertions.*;

class TaskServiceTest {
    @Test
    void testCreateTask() {
        TaskRepository repository = Mockito.mock(TaskRepository.class);
        TaskService service = new TaskService(repository);
        
        Task task = service.createTask("Test Task", "Description");
        assertNotNull(task);
        Mockito.verify(repository).save(Mockito.any(Task.class));
    }

    @Test
    void testGetTask() {
        TaskRepository repository = Mockito.mock(TaskRepository.class);
        TaskService service = new TaskService(repository);
        Task expected = new Task("1", "Test", "Desc");
        Mockito.when(repository.findById("1")).thenReturn(expected);
        
        Task result = service.getTask("1");
        assertEquals(expected, result);
    }
}
