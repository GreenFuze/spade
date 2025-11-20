package main

import (
	"github.com/gin-gonic/gin"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/http"
	"github.com/greenfuze/go-microservices/internal/common/logger"
	"github.com/greenfuze/go-microservices/internal/common/messaging"
)

func main() {
	logger.Info("Starting Notification Service")

	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Error("Failed to load config", logger.GetLogger().Sugar().Fields("error", err)...)
		return
	}

	_, err = messaging.Connect()
	if err != nil {
		logger.Error("Failed to connect to messaging", logger.GetLogger().Sugar().Fields("error", err)...)
	}

	router := http.SetupRouter()

	router.POST("/notifications", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "Notification sent"})
	})

	port := cfg.Server.Port
	if port == "" {
		port = "8085"
	}

	logger.Info("Notification Service listening")
	router.Run(":" + port)
}
