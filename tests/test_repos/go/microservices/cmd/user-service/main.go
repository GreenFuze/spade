package main

import (
	"github.com/gin-gonic/gin"
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/database"
	"github.com/greenfuze/go-microservices/internal/common/http"
	"github.com/greenfuze/go-microservices/internal/common/logger"
	"github.com/greenfuze/go-microservices/internal/common/utils"
	"github.com/greenfuze/go-microservices/pkg/models"
	"github.com/google/uuid"
)

func main() {
	logger.Info("Starting User Service")

	// Initialize Java JVM for text formatting utilities
	// Classpath includes both scala-utils.jar (Scala) and textutils.jar (Java that depends on Scala)
	err := utils.InitJava("internal/common/utils/scalautils.jar:internal/common/utils/textutils.jar")
	if err != nil {
		logger.Error("Failed to initialize Java", logger.GetLogger().Sugar().Fields("error", err)...)
		// Continue anyway - Java is optional
	}
	defer utils.CleanupJava()

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

	router.GET("/users/:id", func(c *gin.Context) {
		id := c.Param("id")
		userID, _ := uuid.Parse(id)
		
		// Use Java utility to format username
		username := "testuser"
		formattedUsername, err := utils.FormatText(username)
		if err == nil {
			username = formattedUsername
		}
		
		user := models.User{
			ID:       userID,
			Email:    "user@example.com",
			Username: username,
		}
		c.JSON(200, user)
	})

	port := cfg.Server.Port
	if port == "" {
		port = "8082"
	}

	logger.Info("User Service listening")
	router.Run(":" + port)
}
