package cache

import (
	"context"
	"github.com/greenfuze/go-microservices/internal/common/database"
	"github.com/greenfuze/go-microservices/internal/common/errors"
	"github.com/redis/go-redis/v9"
)

var rdb *redis.Client

// Connect establishes a Redis connection
func Connect(ctx context.Context) (*redis.Client, error) {
	rdb = redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
	})

	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, err
	}

	return rdb, nil
}

// GetClient returns the Redis client
func GetClient() *redis.Client {
	return rdb
}

// Set stores a value in cache
func Set(ctx context.Context, key string, value interface{}) error {
	if rdb == nil {
		return errors.NewAppError("CACHE_NOT_CONNECTED", "Cache not connected", nil)
	}
	return rdb.Set(ctx, key, value, 0).Err()
}

// Get retrieves a value from cache
func Get(ctx context.Context, key string) (string, error) {
	if rdb == nil {
		return "", errors.NewAppError("CACHE_NOT_CONNECTED", "Cache not connected", nil)
	}
	return rdb.Get(ctx, key).Result()
}
