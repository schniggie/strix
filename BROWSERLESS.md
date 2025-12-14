# Browserless Integration Guide

This guide explains how to integrate Strix with [browserless.io](https://www.browserless.io/) for improved browser automation performance, scalability, and resource management.

## Table of Contents

- [What is Browserless?](#what-is-browserless)
- [Why Use Browserless with Strix?](#why-use-browserless-with-strix)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Deployment Options](#deployment-options)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## What is Browserless?

Browserless is a web service that provides browser automation capabilities through a simple API. It manages browser instances (Chrome, Firefox) in containers and exposes them via WebSocket connections for tools like Playwright and Puppeteer.

### Key Features:
- **Resource Management**: Handles browser lifecycle, memory limits, and cleanup
- **Scalability**: Supports concurrent sessions with configurable limits
- **Performance**: Pre-warmed browser instances for faster startup
- **Monitoring**: Built-in metrics and health checks
- **Security**: Sandboxed browser execution

## Why Use Browserless with Strix?

### Benefits:

1. **Improved Performance**
   - Faster browser startup times with pre-warmed instances
   - Reduced memory overhead on the host system
   - Better resource utilization for concurrent operations

2. **Scalability**
   - Run multiple browser sessions in parallel
   - Horizontal scaling with multiple browserless instances
   - Load balancing support

3. **Resource Isolation**
   - Browser crashes don't affect Strix
   - Configurable memory and CPU limits per session
   - Automatic cleanup of stale sessions

4. **Flexibility**
   - Switch between Chromium and Firefox easily
   - Different browser configurations per instance
   - Support for custom browser arguments

5. **Development & Testing**
   - Consistent browser environment across team members
   - Easy Docker Compose setup for local development
   - Reproducible testing environments

## Quick Start

### Option 1: Docker Compose (Recommended)

The fastest way to get started is using the included Docker Compose configuration:

```bash
# 1. Copy the environment example
cp .env.example .env

# 2. Edit .env and add your LLM configuration
nano .env

# 3. Start the services
docker-compose up -d

# 4. Verify browserless is running
curl http://localhost:3000/pressure

# 5. Run Strix with browserless
docker-compose exec strix bash
```

The Docker Compose setup includes:
- Browserless Chrome on port 3000
- Strix container pre-configured to use browserless
- Health checks and automatic restarts
- Persistent volume for downloads

### Option 2: Manual Setup

If you prefer to run browserless separately:

```bash
# 1. Start browserless
docker run -d \
  --name browserless \
  -p 3000:3000 \
  -e "CONNECTION_TIMEOUT=60000" \
  -e "MAX_CONCURRENT_SESSIONS=10" \
  browserless/chrome:latest

# 2. Configure Strix environment variables
export STRIX_BROWSERLESS_BASE=ws://localhost:3000
export STRIX_BROWSERLESS_TYPE=chromium

# 3. Run Strix as usual
# The browser tool will automatically connect to browserless
```

## Configuration

### Environment Variables

Configure browserless integration using these environment variables:

#### `STRIX_BROWSERLESS_BASE`

**Required for browserless**: WebSocket URL of your browserless instance

```bash
# Local browserless
export STRIX_BROWSERLESS_BASE=ws://localhost:3000

# Docker Compose (internal network)
export STRIX_BROWSERLESS_BASE=ws://browserless:3000

# Remote browserless instance
export STRIX_BROWSERLESS_BASE=ws://browserless.example.com:3000

# With authentication token
export STRIX_BROWSERLESS_BASE=ws://localhost:3000?token=your-token-here
```

**Note**: If not set, Strix will automatically fall back to local browser launch.

#### `STRIX_BROWSERLESS_TYPE`

**Optional**: Browser type to use with browserless

```bash
# Use Chromium (default)
export STRIX_BROWSERLESS_TYPE=chromium

# Use Firefox
export STRIX_BROWSERLESS_TYPE=firefox
```

**Default**: `chromium`

### Verification

To verify your configuration is working:

```bash
# Run the integration test script
python tests/integration/test_browserless_integration.py
```

The script will:
- Check your environment configuration
- Test browser launch and connection
- Test navigation and interaction
- Verify connection stability

## Deployment Options

### 1. Local Development with Docker

Perfect for development and testing:

```yaml
# docker-compose.yml
version: '3.8'
services:
  browserless:
    image: browserless/chrome:latest
    ports:
      - "3000:3000"
    environment:
      - CONNECTION_TIMEOUT=60000
      - MAX_CONCURRENT_SESSIONS=10
```

```bash
docker-compose up -d browserless
export STRIX_BROWSERLESS_BASE=ws://localhost:3000
```

### 2. Production Deployment

For production use, consider:

```yaml
# docker-compose.production.yml
version: '3.8'
services:
  browserless:
    image: browserless/chrome:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    environment:
      - CONNECTION_TIMEOUT=60000
      - MAX_CONCURRENT_SESSIONS=5
      - TOKEN=${BROWSERLESS_TOKEN}
      - PREBOOT_CHROME=true
      - ENABLE_HEAP_DUMP=false
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/pressure"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 3. Kubernetes Deployment

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: browserless
spec:
  replicas: 3
  selector:
    matchLabels:
      app: browserless
  template:
    metadata:
      labels:
        app: browserless
    spec:
      containers:
      - name: browserless
        image: browserless/chrome:latest
        ports:
        - containerPort: 3000
        env:
        - name: CONNECTION_TIMEOUT
          value: "60000"
        - name: MAX_CONCURRENT_SESSIONS
          value: "5"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /pressure
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: browserless
spec:
  selector:
    app: browserless
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
```

### 4. Remote Browserless Instance

Connect to a centralized browserless service:

```bash
# Configure Strix to use remote browserless
export STRIX_BROWSERLESS_BASE=ws://browserless.company.internal:3000
export STRIX_BROWSERLESS_TYPE=chromium

# If authentication is required
export STRIX_BROWSERLESS_BASE=ws://browserless.company.internal:3000?token=${BROWSERLESS_TOKEN}
```

## Testing

### Manual Testing

Use the integration test script to verify functionality:

```bash
# Test with browserless
export STRIX_BROWSERLESS_BASE=ws://localhost:3000
python tests/integration/test_browserless_integration.py

# Test with local browser (no browserless)
unset STRIX_BROWSERLESS_BASE
python tests/integration/test_browserless_integration.py
```

### Automated Testing

For CI/CD pipelines:

```bash
# Start browserless for testing
docker-compose up -d browserless

# Wait for browserless to be ready
timeout 30 bash -c 'until curl -f http://localhost:3000/pressure; do sleep 1; done'

# Run tests
export STRIX_BROWSERLESS_BASE=ws://localhost:3000
python tests/integration/test_browserless_integration.py

# Cleanup
docker-compose down
```

### Test Scenarios

The integration test covers:
1. ✅ Browser launch and initialization
2. ✅ Navigation to URLs
3. ✅ Basic interactions (click, scroll, type)
4. ✅ Connection stability with multiple operations
5. ✅ Fallback to local browser on connection failure

## Troubleshooting

### Connection Issues

#### Problem: Cannot connect to browserless

**Symptoms**:
```
Failed to connect to browserless instance: Connection refused
Falling back to local browser launch
```

**Solutions**:
1. Verify browserless is running:
   ```bash
   curl http://localhost:3000/pressure
   ```

2. Check the WebSocket URL format:
   ```bash
   # Correct formats
   ws://localhost:3000
   ws://browserless:3000
   
   # Incorrect (missing ws://)
   localhost:3000
   http://localhost:3000
   ```

3. Verify network connectivity:
   ```bash
   # From Strix container
   ping browserless
   curl http://browserless:3000/pressure
   ```

#### Problem: Connection timeout

**Symptoms**:
```
Connection to browserless timed out
```

**Solutions**:
1. Increase browserless timeout:
   ```yaml
   environment:
     - CONNECTION_TIMEOUT=120000  # 2 minutes
   ```

2. Check browserless load:
   ```bash
   curl http://localhost:3000/pressure
   ```

3. Verify resource limits aren't being hit:
   ```bash
   docker stats browserless
   ```

### Browser Issues

#### Problem: Browser type not supported

**Symptoms**:
```
Unknown browser type 'safari', defaulting to chromium
```

**Solution**: Only `chromium` and `firefox` are supported:
```bash
export STRIX_BROWSERLESS_TYPE=chromium  # or firefox
```

#### Problem: Browser crashes or hangs

**Solutions**:
1. Increase memory limits:
   ```yaml
   services:
     browserless:
       deploy:
         resources:
           limits:
             memory: 4G  # Increase from default
   ```

2. Reduce concurrent sessions:
   ```yaml
   environment:
     - MAX_CONCURRENT_SESSIONS=3  # Reduce from 10
   ```

3. Enable browser restart on failure:
   ```yaml
   restart: unless-stopped
   ```

### Performance Issues

#### Problem: Slow browser startup

**Solutions**:
1. Enable Chrome preboot:
   ```yaml
   environment:
     - PREBOOT_CHROME=true
   ```

2. Use browserless with SSD storage

3. Increase browserless instances for parallel operations

#### Problem: High memory usage

**Solutions**:
1. Set memory limits per session:
   ```yaml
   environment:
     - MAX_MEMORY_PERCENT=90
   ```

2. Enable session cleanup:
   ```yaml
   environment:
     - SESSION_CHECK_INTERVAL=10000
   ```

3. Monitor and adjust concurrent sessions

### Debugging

Enable debug logging:

```yaml
# In browserless
environment:
  - DEBUG=browserless*
  - DEBUG_DEPTH=4

# In Strix
environment:
  - LOG_LEVEL=DEBUG
```

Check browserless logs:
```bash
docker logs browserless -f
```

Check Strix logs for connection attempts:
```bash
# Look for these log messages:
# INFO: Connecting to browserless instance at ws://...
# INFO: Successfully connected to browserless Chromium
# ERROR: Failed to connect to browserless instance: ...
```

## Advanced Configuration

### Custom Browser Arguments

Browserless supports custom browser arguments:

```yaml
environment:
  - CHROME_ARGS=--disable-gpu,--no-sandbox,--disable-dev-shm-usage
```

### Authentication

Secure your browserless instance with token authentication:

```yaml
# In browserless
environment:
  - TOKEN=your-secure-token-here

# In Strix
export STRIX_BROWSERLESS_BASE=ws://localhost:3000?token=your-secure-token-here
```

### Multiple Browserless Instances

Load balance across multiple instances:

```bash
# Instance 1
docker run -d --name browserless-1 -p 3001:3000 browserless/chrome

# Instance 2
docker run -d --name browserless-2 -p 3002:3000 browserless/chrome

# Configure Strix to use specific instance
export STRIX_BROWSERLESS_BASE=ws://localhost:3001  # or 3002
```

### Monitoring

Browserless provides several endpoints for monitoring:

```bash
# Health check
curl http://localhost:3000/pressure

# Metrics (JSON)
curl http://localhost:3000/stats

# WebSocket connections
curl http://localhost:3000/config
```

Integrate with monitoring tools:
- Prometheus: Use browserless metrics exporter
- Grafana: Create dashboards for session tracking
- Alerting: Set up alerts for resource pressure

### Resource Limits

Fine-tune resource allocation:

```yaml
environment:
  # Connection limits
  - MAX_CONCURRENT_SESSIONS=10
  - QUEUE_LENGTH=50
  
  # Timeout settings
  - CONNECTION_TIMEOUT=60000
  - SESSION_TIMEOUT=300000
  
  # Memory management
  - MAX_MEMORY_PERCENT=90
  - KEEP_ALIVE=true
  
  # Performance
  - PREBOOT_CHROME=true
  - DISABLE_AUTO_SET_DOWNLOAD_BEHAVIOR=false
```

## Best Practices

1. **Use Health Checks**: Always configure health checks for production deployments

2. **Set Resource Limits**: Define memory and CPU limits to prevent resource exhaustion

3. **Monitor Performance**: Track session count, memory usage, and connection times

4. **Enable Fallback**: Strix automatically falls back to local browser if browserless is unavailable

5. **Secure Connections**: Use token authentication for production instances

6. **Scale Horizontally**: Run multiple browserless instances for high-load scenarios

7. **Log Management**: Collect and analyze browserless logs for troubleshooting

8. **Test Regularly**: Run integration tests to verify browserless connectivity

9. **Version Pinning**: Use specific browserless image versions in production

10. **Backup Strategy**: Have a fallback plan if browserless service is down

## Resources

- [Browserless Documentation](https://docs.browserless.io/)
- [Browserless GitHub](https://github.com/browserless/chrome)
- [Playwright Documentation](https://playwright.dev/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Support

For issues related to:
- **Strix browserless integration**: Open an issue in the Strix repository
- **Browserless service**: Consult [browserless.io documentation](https://docs.browserless.io/)
- **Playwright API**: See [Playwright documentation](https://playwright.dev/)

---

**Last Updated**: December 2024

