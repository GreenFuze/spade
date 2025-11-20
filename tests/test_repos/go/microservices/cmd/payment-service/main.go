package main

import (
	"github.com/gin-gonic/gin"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/database"
	"github.com/greenfuze/go-microservices/internal/common/http"
	"github.com/greenfuze/go-microservices/internal/common/logger"
	"github.com/greenfuze/go-microservices/internal/common/metrics"
	"github.com/greenfuze/go-microservices/pkg/models"
	"github.com/google/uuid"
)

func main() {
	logger.Info("Starting Payment Service")

	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Error("Failed to load config", logger.GetLogger().Sugar().Fields("error", err)...)
		return
	}

	_, err = database.Connect()
	if err != nil {
		logger.Error("Failed to connect to database", logger.GetLogger().Sugar().Fields("error", err)...)
	}

	router := http.SetupRouter()

	router.POST("/payments", func(c *gin.Context) {
		metrics.RecordRequest("POST", "/payments")
		payment := models.Payment{
			ID:      uuid.New(),
			OrderID: uuid.New(),
			Amount:  100.0,
			Status:  "completed",
		}
		c.JSON(200, payment)
	})

	port := cfg.Server.Port
	if port == "" {
		port = "8084"
	}

	logger.Info("Payment Service listening")
	router.Run(":" + port)
}
