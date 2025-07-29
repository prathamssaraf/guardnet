# Build stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Install wget for health checks
RUN apk add --no-cache wget

# Copy built application from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create non-root user for nginx
RUN addgroup -g 1001 -S guardnet && \
    adduser -u 1001 -S guardnet -G guardnet

# Change ownership of nginx directories and create necessary dirs
RUN chown -R guardnet:guardnet /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html && \
    mkdir -p /var/cache/nginx/client_temp && \
    chown -R guardnet:guardnet /var/cache/nginx/client_temp

# Don't switch to non-root user for nginx to avoid permission issues
# USER guardnet

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]