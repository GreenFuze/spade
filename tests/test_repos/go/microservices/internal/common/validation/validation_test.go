package validation

import "testing"

func TestValidateEmail(t *testing.T) {
	if !ValidateEmail("test@example.com") {
		t.Error("Valid email failed validation")
	}
	if ValidateEmail("invalid-email") {
		t.Error("Invalid email passed validation")
	}
}

func TestValidateRequired(t *testing.T) {
	if !ValidateRequired("non-empty") {
		t.Error("Non-empty field failed validation")
	}
	if ValidateRequired("") {
		t.Error("Empty field passed validation")
	}
}
