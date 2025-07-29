package cache

import (
	"context"
	"fmt"
	"time"

	"github.com/go-redis/redis/v8"
)

// RedisClient wraps the Redis client with DNS filtering specific methods
type RedisClient struct {
	client *redis.Client
	ctx    context.Context
}

// NewRedisClient creates a new Redis client connection
func NewRedisClient(redisURL string) (*RedisClient, error) {
	// Parse Redis URL (redis://host:port)
	opts, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("failed to parse Redis URL: %w", err)
	}

	// Set connection pool settings
	opts.PoolSize = 10
	opts.MinIdleConns = 2
	opts.MaxConnAge = 30 * time.Minute
	opts.PoolTimeout = 5 * time.Second
	opts.IdleTimeout = 5 * time.Minute
	opts.IdleCheckFrequency = time.Minute

	client := redis.NewClient(opts)
	ctx := context.Background()

	// Test the connection
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to ping Redis: %w", err)
	}

	return &RedisClient{
		client: client,
		ctx:    ctx,
	}, nil
}

// Close closes the Redis connection
func (r *RedisClient) Close() error {
	if r.client != nil {
		return r.client.Close()
	}
	return nil
}

// Get retrieves a value from Redis
func (r *RedisClient) Get(key string) (string, error) {
	val, err := r.client.Get(r.ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return "", fmt.Errorf("key not found: %s", key)
		}
		return "", fmt.Errorf("failed to get key %s: %w", key, err)
	}
	return val, nil
}

// Set stores a value in Redis with expiration
func (r *RedisClient) Set(key, value string, expiration time.Duration) error {
	err := r.client.Set(r.ctx, key, value, expiration).Err()
	if err != nil {
		return fmt.Errorf("failed to set key %s: %w", key, err)
	}
	return nil
}

// Delete removes a key from Redis
func (r *RedisClient) Delete(key string) error {
	err := r.client.Del(r.ctx, key).Err()
	if err != nil {
		return fmt.Errorf("failed to delete key %s: %w", key, err)
	}
	return nil
}

// Exists checks if a key exists in Redis
func (r *RedisClient) Exists(key string) (bool, error) {
	count, err := r.client.Exists(r.ctx, key).Result()
	if err != nil {
		return false, fmt.Errorf("failed to check key existence %s: %w", key, err)
	}
	return count > 0, nil
}

// SetNX sets a key only if it doesn't exist (for locking)
func (r *RedisClient) SetNX(key, value string, expiration time.Duration) (bool, error) {
	success, err := r.client.SetNX(r.ctx, key, value, expiration).Result()
	if err != nil {
		return false, fmt.Errorf("failed to setnx key %s: %w", key, err)
	}
	return success, nil
}

// Increment increments a counter in Redis
func (r *RedisClient) Increment(key string) (int64, error) {
	count, err := r.client.Incr(r.ctx, key).Result()
	if err != nil {
		return 0, fmt.Errorf("failed to increment key %s: %w", key, err)
	}
	return count, nil
}

// IncrementWithExpiry increments a counter and sets expiry if it's a new key
func (r *RedisClient) IncrementWithExpiry(key string, expiration time.Duration) (int64, error) {
	pipe := r.client.TxPipeline()
	
	incrCmd := pipe.Incr(r.ctx, key)
	pipe.Expire(r.ctx, key, expiration)
	
	_, err := pipe.Exec(r.ctx)
	if err != nil {
		return 0, fmt.Errorf("failed to increment with expiry key %s: %w", key, err)
	}
	
	return incrCmd.Val(), nil
}

// GetTTL returns the time to live for a key
func (r *RedisClient) GetTTL(key string) (time.Duration, error) {
	ttl, err := r.client.TTL(r.ctx, key).Result()
	if err != nil {
		return 0, fmt.Errorf("failed to get TTL for key %s: %w", key, err)
	}
	return ttl, nil
}

// SetHash stores a hash in Redis
func (r *RedisClient) SetHash(key string, fields map[string]interface{}) error {
	err := r.client.HMSet(r.ctx, key, fields).Err()
	if err != nil {
		return fmt.Errorf("failed to set hash %s: %w", key, err)
	}
	return nil
}

// GetHash retrieves a hash from Redis
func (r *RedisClient) GetHash(key string) (map[string]string, error) {
	hash, err := r.client.HGetAll(r.ctx, key).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to get hash %s: %w", key, err)
	}
	return hash, nil
}

// GetHashField retrieves a specific field from a hash
func (r *RedisClient) GetHashField(key, field string) (string, error) {
	val, err := r.client.HGet(r.ctx, key, field).Result()
	if err != nil {
		if err == redis.Nil {
			return "", fmt.Errorf("hash field not found: %s.%s", key, field)
		}
		return "", fmt.Errorf("failed to get hash field %s.%s: %w", key, field, err)
	}
	return val, nil
}

// AddToSet adds a member to a set
func (r *RedisClient) AddToSet(key, member string) error {
	err := r.client.SAdd(r.ctx, key, member).Err()
	if err != nil {
		return fmt.Errorf("failed to add to set %s: %w", key, err)
	}
	return nil
}

// IsInSet checks if a member is in a set
func (r *RedisClient) IsInSet(key, member string) (bool, error) {
	exists, err := r.client.SIsMember(r.ctx, key, member).Result()
	if err != nil {
		return false, fmt.Errorf("failed to check set membership %s: %w", key, err)
	}
	return exists, nil
}

// GetSetMembers returns all members of a set
func (r *RedisClient) GetSetMembers(key string) ([]string, error) {
	members, err := r.client.SMembers(r.ctx, key).Result()
	if err != nil {
		return nil, fmt.Errorf("failed to get set members %s: %w", key, err)
	}
	return members, nil
}

// FlushDB clears all keys from the current database (use with caution)
func (r *RedisClient) FlushDB() error {
	err := r.client.FlushDB(r.ctx).Err()
	if err != nil {
		return fmt.Errorf("failed to flush database: %w", err)
	}
	return nil
}

// GetInfo returns Redis server information
func (r *RedisClient) GetInfo() (string, error) {
	info, err := r.client.Info(r.ctx).Result()
	if err != nil {
		return "", fmt.Errorf("failed to get Redis info: %w", err)
	}
	return info, nil
}