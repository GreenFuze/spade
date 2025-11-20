package http

import "testing"

func TestSetupRouter(t *testing.T) {
	router := SetupRouter()
	if router == nil {
		t.Error("SetupRouter returned nil")
	}
}
