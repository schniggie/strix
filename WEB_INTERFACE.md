# Strix Web Interface

A self-service web interface for developers to run penetration tests using the Strix cybersecurity agent.

## Overview

The Strix Web Interface provides the same functionality as the CLI headless mode but through an intuitive web interface. Developers can:

- Submit target URLs for penetration testing
- Optionally provide repository URLs for white-box testing
- Add focused test instructions to guide the scan
- Monitor real-time progress and vulnerability discoveries
- Download comprehensive reports

## Features

### 🌐 Web Interface
- **Modern responsive design** - Works on desktop, tablet, and mobile
- **Real-time updates** - Live progress tracking via WebSocket
- **Vulnerability visualization** - Color-coded severity levels
- **Report generation** - Downloadable text reports
- **Form validation** - Client and server-side input validation

### 🔒 Security
- **Input validation** - Comprehensive URL and instruction sanitization
- **Rate limiting** - Protection against abuse (20 requests per 5 minutes)
- **Security headers** - XSS, CSRF, and clickjacking protection
- **Private network blocking** - Prevents scanning of internal resources

### 🚀 API
- **RESTful endpoints** - Standard HTTP methods for scan management
- **WebSocket support** - Real-time bidirectional communication
- **OpenAPI documentation** - Auto-generated API docs at `/api/docs`
- **Health checks** - Monitoring endpoints for deployment

## Quick Start

### Prerequisites

1. **Environment Variables** (same as CLI):
   ```bash
   export STRIX_LLM="openai/gpt-5"
   export LLM_API_KEY="your-api-key"
   ```

2. **Docker** - Must be running and accessible

3. **Python Dependencies** - Installed via poetry or pip:
   ```bash
   pip install fastapi uvicorn pydantic
   ```

### Starting the Web Interface

1. **Using the CLI command** (recommended):
   ```bash
   strix-web
   ```

2. **Using Python module**:
   ```bash
   python -m strix.interface.web.server
   ```

3. **Custom host/port**:
   ```bash
   strix-web --host 0.0.0.0 --port 8080
   ```

4. **Development mode** (with auto-reload):
   ```bash
   strix-web --debug --reload
   ```

### Accessing the Interface

- **Web Interface**: http://localhost:12000
- **API Documentation**: http://localhost:12000/api/docs
- **Health Check**: http://localhost:12000/health

## Usage

### Web Interface

1. **Open the web interface** in your browser
2. **Fill out the form**:
   - **Target URL** (required): The application you want to test
   - **Repository URL** (optional): For white-box testing with source code
   - **Instructions** (optional): Specific testing focus or credentials
3. **Click "Start Penetration Test"**
4. **Monitor progress** in real-time
5. **Review vulnerabilities** as they're discovered
6. **Download the final report**

### Example Inputs

**Basic Web Application Test**:
- Target URL: `https://myapp.example.com`
- Instructions: `Focus on authentication and authorization vulnerabilities`

**White-box Testing**:
- Target URL: `https://staging.myapp.com`
- Repository URL: `https://github.com/mycompany/myapp`
- Instructions: `Test with admin credentials: admin@example.com / password123`

**API Testing**:
- Target URL: `https://api.myapp.com`
- Instructions: `Focus on REST API endpoints, test for injection vulnerabilities`

## API Reference

### Endpoints

#### Create Scan
```http
POST /api/scans
Content-Type: application/json

{
  "target_url": "https://example.com",
  "repo_url": "https://github.com/user/repo",
  "instructions": "Focus on authentication"
}
```

#### Start Scan
```http
POST /api/scans/{scan_id}/start
```

#### Get Scan Status
```http
GET /api/scans/{scan_id}
```

#### Get Scan Result
```http
GET /api/scans/{scan_id}/result
```

#### List All Scans
```http
GET /api/scans
```

#### Cancel Scan
```http
POST /api/scans/{scan_id}/cancel
```

#### WebSocket Connection
```
WS /api/scans/{scan_id}/ws
```

### WebSocket Messages

The WebSocket connection sends real-time updates:

```json
{
  "type": "progress",
  "scan_id": "uuid",
  "message": "Starting penetration test...",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

```json
{
  "type": "vulnerability",
  "scan_id": "uuid",
  "vulnerability": {
    "report_id": "VULN-001",
    "title": "SQL Injection in Login Form",
    "severity": "high",
    "content": "Detailed vulnerability description...",
    "found_at": "2024-01-01T12:05:00Z"
  },
  "timestamp": "2024-01-01T12:05:00Z"
}
```

```json
{
  "type": "completion",
  "scan_id": "uuid",
  "result": {
    "scan_id": "uuid",
    "status": "completed",
    "vulnerabilities": [...],
    "final_report": "Complete penetration test report..."
  },
  "timestamp": "2024-01-01T12:30:00Z"
}
```

## Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `STRIX_LLM` | Yes | LLM model to use | `openai/gpt-5` |
| `LLM_API_KEY` | Yes* | API key for LLM provider | `sk-...` |
| `LLM_API_BASE` | No | Custom API base URL | `http://localhost:11434` |
| `PERPLEXITY_API_KEY` | No | For enhanced web search | `pplx-...` |

*Required unless using local models with `LLM_API_BASE`

### Command Line Options

```bash
strix-web --help
```

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `0.0.0.0` | Host to bind the server |
| `--port` | `12000` | Port to bind the server |
| `--debug` | `False` | Enable debug logging |
| `--reload` | `False` | Enable auto-reload for development |

### Security Configuration

The web interface includes several security measures:

- **Rate Limiting**: 20 requests per 5 minutes per IP
- **Input Validation**: URL format and content validation
- **Security Headers**: XSS, CSRF, and clickjacking protection
- **Private Network Blocking**: Prevents scanning localhost/private IPs

## Deployment

### Production Deployment

1. **Use a reverse proxy** (nginx, Apache) for SSL termination
2. **Set appropriate environment variables**
3. **Configure firewall** to restrict access as needed
4. **Monitor logs** for security events

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 12000
CMD ["strix-web", "--host", "0.0.0.0", "--port", "12000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strix-web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: strix-web
  template:
    metadata:
      labels:
        app: strix-web
    spec:
      containers:
      - name: strix-web
        image: strix-web:latest
        ports:
        - containerPort: 12000
        env:
        - name: STRIX_LLM
          value: "openai/gpt-5"
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: strix-secrets
              key: llm-api-key
---
apiVersion: v1
kind: Service
metadata:
  name: strix-web-service
spec:
  selector:
    app: strix-web
  ports:
  - port: 80
    targetPort: 12000
  type: LoadBalancer
```

## Development

### Project Structure

```
strix/interface/web/
├── __init__.py
├── api.py              # FastAPI application and endpoints
├── models.py           # Pydantic data models
├── scan_manager.py     # Scan lifecycle management
├── security.py         # Security utilities and validation
├── server.py           # Web server entry point
├── static/
│   ├── css/
│   │   └── style.css   # Frontend styles
│   └── js/
│       └── app.js      # Frontend JavaScript
└── templates/
    └── index.html      # Main web interface template
```

### Adding New Features

1. **Models**: Add new Pydantic models in `models.py`
2. **API Endpoints**: Add new routes in `api.py`
3. **Frontend**: Update HTML/CSS/JS in `static/` and `templates/`
4. **Security**: Add validation in `security.py`

### Testing

Run the test suite:
```bash
python test_web_interface.py
```

### Contributing

1. Follow the existing code style and patterns
2. Add appropriate error handling and logging
3. Update documentation for new features
4. Test thoroughly with various inputs

## Troubleshooting

### Common Issues

**"Module not found" errors**:
- Ensure all dependencies are installed: `pip install fastapi uvicorn pydantic`
- Check that the Strix package is properly installed

**"Docker connection failed"**:
- Ensure Docker is running: `docker ps`
- Check Docker permissions for your user

**"Rate limit exceeded"**:
- Wait 5 minutes between scan attempts
- Contact administrator if limits need adjustment

**WebSocket connection issues**:
- Check firewall settings for WebSocket traffic
- Ensure proxy configuration allows WebSocket upgrades

### Logs

Enable debug logging for troubleshooting:
```bash
strix-web --debug
```

Logs include:
- Request/response details
- Scan progress and errors
- Security validation failures
- WebSocket connection events

## Security Considerations

### Input Validation

All user inputs are validated:
- URLs must use HTTP/HTTPS schemes
- Private/local addresses are blocked
- Repository URLs must match supported patterns
- Instructions are checked for dangerous content

### Rate Limiting

- 20 requests per 5 minutes per IP address
- Prevents abuse and resource exhaustion
- Configurable in `security.py`

### Network Security

- Blocks scanning of private networks (10.x.x.x, 192.168.x.x, etc.)
- Prevents localhost and loopback scanning
- Validates URL schemes and formats

### Web Security

- Content Security Policy headers
- XSS protection headers
- CSRF protection
- Clickjacking prevention
- Secure cookie settings (when using HTTPS)

## Support

For issues, questions, or contributions:

- **GitHub Issues**: https://github.com/usestrix/strix/issues
- **Discord Community**: https://discord.gg/J48Fzuh7
- **Documentation**: https://docs.usestrix.com

## License

Apache 2.0 License - see LICENSE file for details.