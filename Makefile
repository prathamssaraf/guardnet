.PHONY: help install dev test build clean deploy

# Default target
help:
	@echo "GuardNet Development Commands"
	@echo "============================"
	@echo "install     - Install all dependencies"
	@echo "dev         - Start development environment"
	@echo "test        - Run all tests"
	@echo "build       - Build all services"
	@echo "clean       - Clean build artifacts"
	@echo "deploy      - Deploy to production"

# Install dependencies for all services
install:
	@echo "Installing Go dependencies..."
	cd services/dns-filter && go mod tidy
	@echo "Installing Node.js dependencies..."
	cd services/api-gateway && npm install
	cd services/dashboard && npm install

# Start development environment
dev:
	@echo "Starting GuardNet development environment..."
	docker-compose up --build

# Run tests
test:
	@echo "Running Go tests..."
	cd services/dns-filter && go test ./...
	@echo "Running Node.js tests..."
	cd services/api-gateway && npm test
	cd services/dashboard && npm test

# Build all services
build:
	@echo "Building DNS Filter service..."
	cd services/dns-filter && go build -o bin/dns-filter ./cmd/server
	@echo "Building API Gateway..."
	cd services/api-gateway && npm run build
	@echo "Building Dashboard..."
	cd services/dashboard && npm run build

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf services/dns-filter/bin
	rm -rf services/api-gateway/dist
	rm -rf services/dashboard/build

# Deploy to production
deploy:
	@echo "Deploying to production..."
	kubectl apply -f infrastructure/kubernetes/