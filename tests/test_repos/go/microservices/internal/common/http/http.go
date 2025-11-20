package http

import (
	"github.com/gin-gonic/gin"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/logger"
)

// SetupRouter sets up a Gin router with middleware
func SetupRouter() *gin.Engine {
	cfg := config.GetConfig()
	if cfg == nil {
		logger.Error("Config not loaded")
		return gin.Default()
	}

	router := gin.Default()

	// Add middleware
	router.Use(LoggerMiddleware())
	router.Use(RecoveryMiddleware())

	return router
}

// LoggerMiddleware provides request logging
func LoggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		logger.Info("HTTP request")
		c.Next()
	}
}

// RecoveryMiddleware provides panic recovery
func RecoveryMiddleware() gin.HandlerFunc {
	return gin.Recovery()
}
