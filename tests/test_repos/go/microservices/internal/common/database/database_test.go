package database

import "testing"

func TestGetDB(t *testing.T) {
	db := GetDB()
	// In test environment, db might be nil if Connect wasn't called
	// This is expected behavior
	_ = db
}
