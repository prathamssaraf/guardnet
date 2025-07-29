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

# Build the application (static binary for better compatibility)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -a -installsuffix cgo -o bin/dns-filter ./cmd/server

# Final stage - using ubuntu for better compatibility
FROM ubuntu:20.04

# Install ca-certificates and create user
RUN apt-get update && \
    apt-get install -y ca-certificates wget && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -g 1001 guardnet && \
    useradd -u 1001 -g guardnet -m guardnet

# Set working directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /app/bin/dns-filter /app/dns-filter

# Copy any config files if needed
COPY --from=builder /app/configs ./configs

# Ensure binary has execute permissions and change ownership
RUN chmod +x /app/dns-filter && \
    chown -R guardnet:guardnet /app

# Don't switch to non-root user for now (troubleshooting)
# USER guardnet

# Expose ports
EXPOSE 53/udp 8080/tcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Use CMD instead of ENTRYPOINT for better compatibility
CMD ["/app/dns-filter"]