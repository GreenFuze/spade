package main

import (
	"github.com/gin-gonic/gin"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/http"
	"github.com/greenfuze/go-microservices/internal/common/logger"
	"github.com/greenfuze/go-microservices/pkg/auth"
	"github.com/google/uuid"
)

func main() {
	logger.Info("Starting Auth Service")

	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Error("Failed to load config", logger.GetLogger().Sugar().Fields("error", err)...)
		return
	}

	router := http.SetupRouter()

	router.POST("/auth/login", func(c *gin.Context) {
		userID := uuid.New()
		token, err := auth.GenerateToken(userID, "secret-key")
		if err != nil {
			c.JSON(500, gin.H{"error": "Failed to generate token"})
			return
		}
		c.JSON(200, gin.H{"token": token})
	})

	port := cfg.Server.Port
	if port == "" {
		port = "8081"
	}

	logger.Info("Auth Service listening")
	router.Run(":" + port)
}
