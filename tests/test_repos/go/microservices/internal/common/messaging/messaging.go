package messaging

import (
	"github.com/greenfuze/go-microservices/internal/common/config"
	"github.com/greenfuze/go-microservices/internal/common/logger"
	"github.com/nats-io/nats.go"
)

var nc *nats.Conn

// Connect establishes a NATS connection
func Connect() (*nats.Conn, error) {
	cfg := config.GetConfig()
	if cfg == nil {
		return nil, logger.GetLogger().Sugar().Error("Config not loaded")
	}

	url := cfg.NATS.URL
	if url == "" {
		url = nats.DefaultURL
	}

	var err error
	nc, err = nats.Connect(url)
	if err != nil {
		return nil, err
	}

	logger.Info("NATS connection established")
	return nc, nil
}

// GetConn returns the NATS connection
func GetConn() *nats.Conn {
	return nc
}

// Publish publishes a message to a subject
func Publish(subject string, data []byte) error {
	if nc == nil {
		logger.Error("NATS not connected")
		return errors.New("NATS not connected")
	}
	return nc.Publish(subject, data)
}

// Subscribe subscribes to a subject
func Subscribe(subject string, handler nats.MsgHandler) (*nats.Subscription, error) {
	if nc == nil {
		logger.Error("NATS not connected")
		return nil, errors.New("NATS not connected")
	}
	return nc.Subscribe(subject, handler)
}

// Close closes the NATS connection
func Close() {
	if nc != nil {
		nc.Close()
	}
}
