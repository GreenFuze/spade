package main

import (
	"github.com/gin-gonic/gin"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/http"
	"github.com/greenfuze/go-microservices/internal/common/logger"
)

func main() {
	logger.Info("Starting API Gateway")

	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Error("Failed to load config", logger.GetLogger().Sugar().Fields("error", err)...)
		return
	}

	router := http.SetupRouter()

	router.GET("/health", func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	})

	port := cfg.Server.Port
	if port == "" {
		port = "8080"
	}

	logger.Info("API Gateway listening")
	router.Run(":" + port)
}
