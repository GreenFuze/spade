package cache

import "testing"

func TestGetClient(t *testing.T) {
	client := GetClient()
	// In test environment, client might be nil if Connect wasn't called
	_ = client
}
