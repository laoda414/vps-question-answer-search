#!/bin/bash

#==============================================================================
# QA Search Application Deployment Script
#==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backups"
COMPOSE_FILE="docker-compose.prod.yml"

echo "=================================================="
echo "QA Search Application Deployment"
echo "=================================================="
echo ""

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: Running as root is not recommended${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env.production exists
if [ ! -f "$PROJECT_DIR/.env.production" ]; then
    echo -e "${RED}❌ Error: .env.production file not found${NC}"
    echo "Please create .env.production from .env.production.example"
    exit 1
fi

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Backup database before deployment
echo -e "${YELLOW}📦 Creating database backup...${NC}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "$PROJECT_DIR/data/qa_search.db" ]; then
    cp "$PROJECT_DIR/data/qa_search.db" "$BACKUP_DIR/qa_search_$TIMESTAMP.db"
    echo -e "${GREEN}✅ Database backup created: qa_search_$TIMESTAMP.db${NC}"
else
    echo -e "${YELLOW}⚠️  No database found to backup${NC}"
fi

# Pull latest changes (if in git repo)
if [ -d "$PROJECT_DIR/.git" ]; then
    echo -e "${YELLOW}📥 Pulling latest changes...${NC}"
    cd "$PROJECT_DIR"
    git pull origin main || echo -e "${YELLOW}⚠️  Git pull failed or not needed${NC}"
fi

# Build and start containers
echo -e "${YELLOW}🔨 Building Docker images...${NC}"
cd "$PROJECT_DIR"
docker-compose -f "$COMPOSE_FILE" build --no-cache

echo -e "${YELLOW}🚀 Starting containers...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check service health
echo -e "${YELLOW}🔍 Checking service health...${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Test API endpoint
echo -e "${YELLOW}🧪 Testing API endpoint...${NC}"
if curl -f -s http://localhost/api/health > /dev/null; then
    echo -e "${GREEN}✅ API is responding${NC}"
else
    echo -e "${RED}❌ API health check failed${NC}"
fi

# Show logs
echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "To view logs, run:"
echo "  docker-compose -f $COMPOSE_FILE logs -f"
echo ""
echo "To stop services, run:"
echo "  docker-compose -f $COMPOSE_FILE down"
echo ""
echo "To restart services, run:"
echo "  docker-compose -f $COMPOSE_FILE restart"
echo ""
