package models

import "github.com/google/uuid"

// User represents a user model
type User struct {
	ID       uuid.UUID `json:"id"`
	Email    string    `json:"email"`
	Username string    `json:"username"`
}

// Order represents an order model
type Order struct {
	ID     uuid.UUID `json:"id"`
	UserID uuid.UUID `json:"user_id"`
	Amount float64   `json:"amount"`
	Status string    `json:"status"`
}

// Payment represents a payment model
type Payment struct {
	ID      uuid.UUID `json:"id"`
	OrderID uuid.UUID `json:"order_id"`
	Amount  float64   `json:"amount"`
	Status  string    `json:"status"`
}
