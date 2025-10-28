package user

import (
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestService_CreateUser(t *testing.T) {
	service := NewService()
	user := service.CreateUser("john_doe", "john@example.com")

	assert.Equal(t, "john_doe", user.Username)
	assert.Equal(t, "john@example.com", user.Email)
	assert.True(t, user.Active)
	assert.Equal(t, int64(1), user.ID)
}

func TestService_GetUser(t *testing.T) {
	service := NewService()
	createdUser := service.CreateUser("jane_doe", "jane@example.com")

	user, err := service.GetUser(createdUser.ID)
	require.NoError(t, err)
	assert.Equal(t, createdUser, user)

	_, err = service.GetUser(999)
	assert.Error(t, err)
}

func TestService_GetUserByUsername(t *testing.T) {
	service := NewService()
	service.CreateUser("alice", "alice@example.com")

	user, err := service.GetUserByUsername("alice")
	require.NoError(t, err)
	assert.Equal(t, "alice", user.Username)

	_, err = service.GetUserByUsername("bob")
	assert.Error(t, err)
}

func TestService_GetAllUsers(t *testing.T) {
	service := NewService()
	assert.Empty(t, service.GetAllUsers())

	service.CreateUser("user1", "user1@example.com")
	service.CreateUser("user2", "user2@example.com")

	users := service.GetAllUsers()
	assert.Len(t, users, 2)
}

func TestService_UpdateUser(t *testing.T) {
	service := NewService()
	user := service.CreateUser("test_user", "test@example.com")
	user.Email = "updated@example.com"

	err := service.UpdateUser(user)
	require.NoError(t, err)

	updatedUser, err := service.GetUser(user.ID)
	require.NoError(t, err)
	assert.Equal(t, "updated@example.com", updatedUser.Email)
}

func TestService_DeleteUser(t *testing.T) {
	service := NewService()
	user := service.CreateUser("delete_me", "delete@example.com")

	err := service.DeleteUser(user.ID)
	require.NoError(t, err)

	_, err = service.GetUser(user.ID)
	assert.Error(t, err)
}
