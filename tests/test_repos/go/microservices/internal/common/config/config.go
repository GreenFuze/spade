package config

import (
	"github.com/greenfuze/go-microservices/internal/common/logger"
	"github.com/greenfuze/go-microservices/internal/common/validation"
	"github.com/spf13/viper"
)

// Config holds application configuration
type Config struct {
	Server   ServerConfig
	Database DatabaseConfig
	Redis    RedisConfig
	NATS     NATSConfig
}

// ServerConfig holds server configuration
type ServerConfig struct {
	Port string
	Host string
}

// DatabaseConfig holds database configuration
type DatabaseConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	DBName   string
}

// RedisConfig holds Redis configuration
type RedisConfig struct {
	Host string
	Port int
}

// NATSConfig holds NATS configuration
type NATSConfig struct {
	URL string
}

var appConfig *Config

// LoadConfig loads configuration from file and environment
func LoadConfig() (*Config, error) {
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	viper.AddConfigPath(".")
	viper.AddConfigPath("./configs")

	viper.SetDefault("server.port", "8080")
	viper.SetDefault("server.host", "localhost")

	if err := viper.ReadInConfig(); err != nil {
		logger.Info("Config file not found, using defaults")
	}

	viper.AutomaticEnv()

	config := &Config{}
	if err := viper.Unmarshal(config); err != nil {
		return nil, err
	}

	if err := validation.ValidateStruct(config); err != nil {
		return nil, err
	}

	appConfig = config
	return config, nil
}

// GetConfig returns the loaded configuration
func GetConfig() *Config {
	return appConfig
}
