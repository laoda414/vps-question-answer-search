#!/bin/bash

#==============================================================================
# QA Search Application - GitHub Deployment Script
#==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/qa-investment-search"
BACKUP_DIR="$PROJECT_DIR/backups"
COMPOSE_FILE="docker-compose.prod.yml"
GITHUB_REPO="https://github.com/laoda414/vps-question-answer-search.git"
BRANCH="master"

echo "=================================================="
echo "QA Search - GitHub Deployment"
echo "=================================================="
echo ""

# Check if running in correct directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}❌ Error: Project directory not found: $PROJECT_DIR${NC}"
    echo "Please create the directory first or update PROJECT_DIR in script"
    exit 1
fi

cd "$PROJECT_DIR"

# Check if .env.production exists
if [ ! -f "$PROJECT_DIR/.env.production" ]; then
    echo -e "${RED}❌ Error: .env.production file not found${NC}"
    echo "Please create .env.production from .env.production.example"
    exit 1
fi

# Backup database before deployment
echo -e "${BLUE}📦 Creating database backup...${NC}"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "$PROJECT_DIR/data/qa_search.db" ]; then
    cp "$PROJECT_DIR/data/qa_search.db" "$BACKUP_DIR/qa_search_$TIMESTAMP.db"
    echo -e "${GREEN}✅ Database backup created: qa_search_$TIMESTAMP.db${NC}"

    # Keep only last 10 backups
    cd "$BACKUP_DIR"
    ls -t qa_search_*.db | tail -n +11 | xargs -r rm
    echo -e "${GREEN}✅ Old backups cleaned up (keeping last 10)${NC}"
else
    echo -e "${YELLOW}⚠️  No database found to backup${NC}"
fi

cd "$PROJECT_DIR"

# Pull latest changes from GitHub
echo -e "${BLUE}📥 Pulling latest changes from GitHub...${NC}"
if [ -d "$PROJECT_DIR/.git" ]; then
    # Repository already exists, pull updates
    git fetch origin
    git reset --hard origin/$BRANCH
    echo -e "${GREEN}✅ Code updated from GitHub${NC}"
else
    # First time setup - clone repository
    echo -e "${YELLOW}📦 Cloning repository...${NC}"
    cd $(dirname "$PROJECT_DIR")
    git clone "$GITHUB_REPO" $(basename "$PROJECT_DIR")
    cd "$PROJECT_DIR"
    echo -e "${GREEN}✅ Repository cloned${NC}"
fi

# Show what changed
echo -e "${BLUE}📋 Recent commits:${NC}"
git log -3 --oneline

# Stop existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose -f "$COMPOSE_FILE" down || true

# Build new images
echo -e "${BLUE}🔨 Building Docker images...${NC}"
docker-compose -f "$COMPOSE_FILE" build --no-cache

# Start containers
echo -e "${BLUE}🚀 Starting containers...${NC}"
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be healthy
echo -e "${BLUE}⏳ Waiting for services to be ready...${NC}"
sleep 15

# Check service health
echo -e "${BLUE}🔍 Checking service health...${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Test API endpoint
echo -e "${BLUE}🧪 Testing API endpoint...${NC}"
MAX_RETRIES=5
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://localhost/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is responding${NC}"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT+1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}⏳ API not ready yet, retrying ($RETRY_COUNT/$MAX_RETRIES)...${NC}"
            sleep 5
        else
            echo -e "${RED}❌ API health check failed after $MAX_RETRIES attempts${NC}"
            echo -e "${YELLOW}Check logs: docker-compose -f $COMPOSE_FILE logs backend${NC}"
        fi
    fi
done

# Clean up old Docker images
echo -e "${BLUE}🧹 Cleaning up old Docker images...${NC}"
docker system prune -f

# Show final status
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}📊 Container Status:${NC}"
docker-compose -f "$COMPOSE_FILE" ps
echo ""
echo -e "${BLUE}📝 Useful Commands:${NC}"
echo "  View logs:     docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  Restart:       docker-compose -f $COMPOSE_FILE restart"
echo ""
echo -e "${BLUE}🔗 Access:${NC}"
echo "  Frontend: http://$(hostname -I | awk '{print $1}')"
echo "  API:      http://$(hostname -I | awk '{print $1}')/api/health"
echo ""
