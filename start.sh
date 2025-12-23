#!/bin/bash

# AI Customer Support Automation - Quick Start Script

echo "🚀 AI Customer Support Automation - Quick Start"
echo "================================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo "⚠️  Please edit .env and add your API keys before continuing!"
    echo ""
    echo "Required:"
    echo "  - GROQ_API_KEY"
    echo "  - SUPPORT_EMAIL"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start services
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
echo ""
echo "🔍 Checking service health..."

# Check backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend is not responding yet, may need more time..."
fi

# Check dashboard
if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ Dashboard is ready"
else
    echo "⚠️  Dashboard is not responding yet, may need more time..."
fi

echo ""
echo "================================================"
echo "🎉 Setup Complete!"
echo "================================================"
echo ""
echo "Access your services:"
echo "  📊 Dashboard:  http://localhost:8501"
echo "  🔌 API:        http://localhost:8000"
echo "  📚 API Docs:   http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "  1. Open dashboard: http://localhost:8501"
echo "  2. Click 'Fetch New Emails' to start processing"
echo "  3. Review and approve AI-generated replies"
echo ""
echo "View logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f dashboard"
echo ""
echo "Stop services:"
echo "  docker-compose down"
echo ""
