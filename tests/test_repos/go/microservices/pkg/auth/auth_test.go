package auth

import (
	"testing"
	"github.com/google/uuid"
)

func TestGenerateToken(t *testing.T) {
	userID := uuid.New()
	token, err := GenerateToken(userID, "test-secret")
	if err != nil {
		t.Fatalf("GenerateToken failed: %v", err)
	}
	if token == "" {
		t.Error("GenerateToken returned empty token")
	}
}
