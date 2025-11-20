package validation

import (
	"github.com/go-playground/validator/v10"
)

var validate *validator.Validate

func init() {
	validate = validator.New()
}

// ValidateStruct validates a struct using go-playground/validator
func ValidateStruct(s interface{}) error {
	return validate.Struct(s)
}

// ValidateEmail validates an email address
func ValidateEmail(email string) bool {
	return validate.Var(email, "required,email") == nil
}

// ValidateRequired validates that a field is not empty
func ValidateRequired(field string) bool {
	return validate.Var(field, "required") == nil
}
