package com.example.persistence;

import com.example.domain.Task;
import org.hibernate.Session;
import org.hibernate.SessionFactory;
import org.hibernate.cfg.Configuration;

/**
 * Task repository for database operations.
 */
public class TaskRepository {
    private SessionFactory sessionFactory;

    public TaskRepository() {
        Configuration configuration = new Configuration();
        configuration.configure();
        this.sessionFactory = configuration.buildSessionFactory();
    }

    public void save(Task task) {
        try (Session session = sessionFactory.openSession()) {
            session.beginTransaction();
            session.save(task);
            session.getTransaction().commit();
        }
    }

    public Task findById(String id) {
        try (Session session = sessionFactory.openSession()) {
            return session.get(Task.class, id);
        }
    }
}
