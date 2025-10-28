package user

import (
	"errors"
	"sync"
	"time"
)

// User represents a user in the system.
type User struct {
	ID        int64     `json:"id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
	Active    bool      `json:"active"`
}

// Service manages users.
type Service struct {
	users  map[int64]*User
	nextID int64
	mutex  sync.RWMutex
}

// NewService creates a new user service.
func NewService() *Service {
	return &Service{
		users:  make(map[int64]*User),
		nextID: 1,
	}
}

// CreateUser creates a new user.
func (s *Service) CreateUser(username, email string) *User {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	user := &User{
		ID:        s.nextID,
		Username:  username,
		Email:     email,
		CreatedAt: time.Now(),
		Active:    true,
	}
	s.nextID++

	s.users[user.ID] = user
	return user
}

// GetUser retrieves a user by ID.
func (s *Service) GetUser(id int64) (*User, error) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	user, exists := s.users[id]
	if !exists {
		return nil, errors.New("user not found")
	}
	return user, nil
}

// GetUserByUsername retrieves a user by username.
func (s *Service) GetUserByUsername(username string) (*User, error) {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	for _, user := range s.users {
		if user.Username == username {
			return user, nil
		}
	}
	return nil, errors.New("user not found")
}

// GetAllUsers returns all users.
func (s *Service) GetAllUsers() []*User {
	s.mutex.RLock()
	defer s.mutex.RUnlock()

	users := make([]*User, 0, len(s.users))
	for _, user := range s.users {
		users = append(users, user)
	}
	return users
}

// UpdateUser updates an existing user.
func (s *Service) UpdateUser(user *User) error {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if _, exists := s.users[user.ID]; !exists {
		return errors.New("user not found")
	}

	s.users[user.ID] = user
	return nil
}

// DeleteUser deletes a user by ID.
func (s *Service) DeleteUser(id int64) error {
	s.mutex.Lock()
	defer s.mutex.Unlock()

	if _, exists := s.users[id]; !exists {
		return errors.New("user not found")
	}

	delete(s.users, id)
	return nil
}
