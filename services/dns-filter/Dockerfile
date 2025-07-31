# Build stage
FROM golang:1.21-alpine AS builder

# Install git and ca-certificates for fetching dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application (static binary with explicit platform targeting)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -a -ldflags="-w -s -extldflags '-static'" -installsuffix cgo -o bin/dns-filter ./cmd/server

# Final stage - using scratch for minimal static binary
FROM scratch

# Copy ca-certificates from builder
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy binary from builder stage (use absolute path)
COPY --from=builder /app/bin/dns-filter /dns-filter

# Copy any config files if needed  
COPY --from=builder /app/configs /configs

# Expose ports
EXPOSE 53/udp 8080/tcp

# Health check removed for scratch image (no wget available)

# Use absolute path in CMD
CMD ["/dns-filter"]