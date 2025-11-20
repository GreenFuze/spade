package metrics

import (
	"github.com/greenfuze/go-microservices/internal/common/messaging"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// RequestCounter counts HTTP requests
	RequestCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint"},
	)

	// RequestDuration tracks request duration
	RequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name: "http_request_duration_seconds",
			Help: "HTTP request duration in seconds",
		},
		[]string{"method", "endpoint"},
	)
)

// RecordRequest records a request metric
func RecordRequest(method, endpoint string) {
	RequestCounter.WithLabelValues(method, endpoint).Inc()
}

// RecordDuration records request duration
func RecordDuration(method, endpoint string, duration float64) {
	RequestDuration.WithLabelValues(method, endpoint).Observe(duration)
}

// PublishMetrics publishes metrics via messaging
func PublishMetrics(metrics map[string]float64) error {
	conn := messaging.GetConn()
	if conn == nil {
		return nil
	}
	// In real implementation, serialize and publish metrics
	return nil
}
