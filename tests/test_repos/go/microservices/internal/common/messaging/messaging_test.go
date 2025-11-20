package messaging

import "testing"

func TestGetConn(t *testing.T) {
	conn := GetConn()
	// In test environment, conn might be nil if Connect wasn't called
	_ = conn
}
