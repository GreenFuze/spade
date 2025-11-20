package database

import (
	"database/sql"
	"errors"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/logger"
	_ "github.com/lib/pq"
)

var db *sql.DB

// Connect establishes a database connection
func Connect() (*sql.DB, error) {
	cfg := config.GetConfig()
	if cfg == nil {
		return nil, logger.GetLogger().Sugar().Error("Config not loaded")
	}

	dsn := "postgres://" + cfg.Database.User + ":" + cfg.Database.Password +
		"@" + cfg.Database.Host + ":5432" +
		"/" + cfg.Database.DBName + "?sslmode=disable"

	var err error
	db, err = sql.Open("postgres", dsn)
	if err != nil {
		return nil, err
	}

	if err = db.Ping(); err != nil {
		return nil, err
	}

	logger.Info("Database connection established")
	return db, nil
}

// GetDB returns the database connection
func GetDB() *sql.DB {
	return db
}

// Close closes the database connection
func Close() error {
	if db != nil {
		return db.Close()
	}
	return nil
}
