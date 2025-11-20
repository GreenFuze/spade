package crypto

import "testing"

func TestHashPassword(t *testing.T) {
	hash, err := HashPassword("testpassword")
	if err != nil {
		t.Fatalf("HashPassword failed: %v", err)
	}
	if hash == "" {
		t.Error("HashPassword returned empty hash")
	}
}

func TestCheckPasswordHash(t *testing.T) {
	hash, _ := HashPassword("testpassword")
	if !CheckPasswordHash("testpassword", hash) {
		t.Error("CheckPasswordHash failed for correct password")
	}
	if CheckPasswordHash("wrongpassword", hash) {
		t.Error("CheckPasswordHash succeeded for wrong password")
	}
}
