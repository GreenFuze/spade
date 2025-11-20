package com.example.persistence;

import com.example.domain.Task;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import static org.junit.jupiter.api.Assertions.*;

class PersistenceServiceTest {
    @Test
    void testTaskRepository() {
        TaskRepository repository = Mockito.mock(TaskRepository.class);
        Task task = new Task("1", "Test", "Description");
        Mockito.when(repository.findById("1")).thenReturn(task);
        
        Task result = repository.findById("1");
        assertNotNull(result);
    }
}
