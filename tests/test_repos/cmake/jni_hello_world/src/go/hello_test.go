package main

import (
	"testing"
)

// TestHelloGo tests the HelloGo() function
func TestHelloGo(t *testing.T) {
	// HelloGo prints to stdout, so we just verify it doesn't panic
	// In a real test, we might capture stdout and verify the output
	HelloGo()

	// If we get here without panic, the test passes
	t.Log("HelloGo() executed successfully")
}
