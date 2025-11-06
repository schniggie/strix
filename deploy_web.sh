#!/bin/bash
# Strix Web Interface Deployment Script

set -e

echo "🦉 Strix Web Interface Deployment"
echo "=================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  Warning: Running as root. Consider using a non-root user for security."
fi

# Check for required environment variables
if [[ -z "$STRIX_LLM" ]]; then
    echo "❌ Error: STRIX_LLM environment variable is not set"
    echo "   Example: export STRIX_LLM='openai/gpt-5'"
    exit 1
fi

if [[ -z "$LLM_API_KEY" && -z "$LLM_API_BASE" ]]; then
    echo "❌ Error: Either LLM_API_KEY or LLM_API_BASE must be set"
    echo "   For cloud providers: export LLM_API_KEY='your-api-key'"
    echo "   For local models: export LLM_API_BASE='http://localhost:11434'"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

if ! docker ps &> /dev/null; then
    echo "❌ Error: Cannot connect to Docker daemon"
    echo "   Make sure Docker is running and you have permission to access it"
    exit 1
fi

# Check Python and dependencies
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✅ Environment checks passed"

# Install dependencies if needed
echo "📦 Checking Python dependencies..."
if ! python3 -c "import fastapi, uvicorn, pydantic" &> /dev/null; then
    echo "📦 Installing required dependencies..."
    pip3 install fastapi uvicorn pydantic
else
    echo "✅ Dependencies already installed"
fi

# Set default values
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"12000"}
DEBUG=${DEBUG:-"false"}

echo "🚀 Starting Strix Web Interface..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Debug: $DEBUG"
echo ""
echo "🌐 Web Interface will be available at: http://$HOST:$PORT"
echo "📚 API Documentation will be available at: http://$HOST:$PORT/api/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the web interface
if [[ "$DEBUG" == "true" ]]; then
    python3 -m strix.interface.web.server --host "$HOST" --port "$PORT" --debug
else
    python3 -m strix.interface.web.server --host "$HOST" --port "$PORT"
fi