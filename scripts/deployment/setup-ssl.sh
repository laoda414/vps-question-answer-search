#!/bin/bash

#==============================================================================
# SSL Certificate Setup with Let's Encrypt
#==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=================================================="
echo "SSL Certificate Setup"
echo "=================================================="
echo ""

# Check if certbot is installed
if ! command -v certbot &> /dev/null; then
    echo -e "${YELLOW}📦 Installing certbot...${NC}"
    sudo apt-get update
    sudo apt-get install -y certbot
fi

# Prompt for domain
read -p "Enter your domain name (e.g., example.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}❌ Domain name is required${NC}"
    exit 1
fi

# Prompt for email
read -p "Enter your email for Let's Encrypt notifications: " EMAIL

if [ -z "$EMAIL" ]; then
    echo -e "${RED}❌ Email is required${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}🔐 Obtaining SSL certificate for $DOMAIN...${NC}"
echo ""

# Obtain certificate
sudo certbot certonly --standalone \
    --preferred-challenges http \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# Copy certificates to project
echo -e "${YELLOW}📋 Copying certificates...${NC}"
sudo mkdir -p "$PROJECT_DIR/nginx/ssl"
sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "$PROJECT_DIR/nginx/ssl/"
sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "$PROJECT_DIR/nginx/ssl/"
sudo chown -R $(whoami):$(whoami) "$PROJECT_DIR/nginx/ssl"

# Update nginx configuration
echo -e "${YELLOW}⚙️  Updating nginx configuration...${NC}"
sed -i "s/your-domain.com/$DOMAIN/g" "$PROJECT_DIR/nginx/conf.d/qa-search.conf"

echo ""
echo -e "${GREEN}✅ SSL certificate setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review and update nginx/conf.d/qa-search.conf if needed"
echo "2. Run ./scripts/deployment/deploy.sh to deploy with HTTPS"
echo ""
echo "Certificate will expire in 90 days. Set up auto-renewal:"
echo "  sudo certbot renew --dry-run"
echo ""
