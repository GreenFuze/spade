package main

import (
	"github.com/gin-gonic/gin"
	"github.com/greenfuze/go-microservices/internal/common/cache"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/database"
	"github.com/greenfuze/go-microservices/internal/common/http"
	"github.com/greenfuze/go-microservices/internal/common/logger"
	"github.com/greenfuze/go-microservices/internal/common/messaging"
	"github.com/greenfuze/go-microservices/pkg/models"
	"github.com/google/uuid"
	"context"
)

func main() {
	logger.Info("Starting Order Service")

	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Error("Failed to load config")
		return
	}

	_, err = database.Connect()
	if err != nil {
		logger.Error("Failed to connect to database")
	}

	_, err = messaging.Connect()
	if err != nil {
		logger.Error("Failed to connect to messaging")
	}

	_, err = cache.Connect(context.Background())
	if err != nil {
		logger.Error("Failed to connect to cache")
	}

	router := http.SetupRouter()

	router.POST("/orders", func(c *gin.Context) {
		order := models.Order{
			ID:     uuid.New(),
			UserID: uuid.New(),
			Amount: 100.0,
			Status: "pending",
		}
		c.JSON(200, order)
	})

	port := cfg.Server.Port
	if port == "" {
		port = "8083"
	}

	logger.Info("Order Service listening")
	router.Run(":" + port)
}
