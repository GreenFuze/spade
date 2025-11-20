package metrics

import "testing"

func TestRecordRequest(t *testing.T) {
	RecordRequest("GET", "/test")
}

func TestRecordDuration(t *testing.T) {
	RecordDuration("GET", "/test", 0.1)
}
