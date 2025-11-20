package logger

import "testing"

func TestGetLogger(t *testing.T) {
	log := GetLogger()
	if log == nil {
		t.Error("GetLogger returned nil")
	}
}

func TestInfo(t *testing.T) {
	Info("test message")
}
