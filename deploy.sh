#!/bin/bash

# Employee Discounts Agent - Cloud Run Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Employee Discounts Multi-Agent System - Cloud Run Deploy${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed${NC}"
    echo "Please install from: https://cloud.google.com/sdk"
    exit 1
fi

# Get GCP project ID
PROJECT_ID=$(gcloud config get-value project)

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project configured${NC}"
    echo "Set project: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✅ GCP Project: ${PROJECT_ID}${NC}"

# Service configuration
SERVICE_NAME="employee-discounts-agent"
REGION="us-central1"
MEMORY="512Mi"
CPU="1"
TIMEOUT="3600"

echo -e "\n${BLUE}📋 Deployment Configuration:${NC}"
echo "  Service Name: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  Memory: $MEMORY"
echo "  CPU: $CPU"
echo "  Timeout: ${TIMEOUT}s"

# Build Docker image
echo -e "\n${BLUE}🔨 Building Docker image...${NC}"

IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

docker build -t ${IMAGE_NAME} .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Docker build failed${NC}"
    exit 1
fi

# Push to Container Registry
echo -e "\n${BLUE}📤 Pushing to Container Registry...${NC}"

docker push ${IMAGE_NAME}

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Image pushed successfully${NC}"
else
    echo -e "${RED}❌ Push failed${NC}"
    exit 1
fi

# Deploy to Cloud Run
echo -e "\n${BLUE}🚀 Deploying to Cloud Run...${NC}"

gcloud run deploy ${SERVICE_NAME} \
    --image=${IMAGE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --memory=${MEMORY} \
    --cpu=${CPU} \
    --timeout=${TIMEOUT} \
    --allow-unauthenticated \
    --set-env-vars="LOG_LEVEL=INFO" \
    --no-gen2

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Deployed to Cloud Run successfully${NC}"
else
    echo -e "${RED}❌ Deployment failed${NC}"
    exit 1
fi

# Get service URL
echo -e "\n${BLUE}📍 Getting service URL...${NC}"

SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform=managed \
    --region=${REGION} \
    --format='value(status.url)')

echo -e "${GREEN}✅ Service URL: ${SERVICE_URL}${NC}"

# Test the deployment
echo -e "\n${BLUE}✨ Testing deployment...${NC}"

sleep 5  # Wait for service to be ready

HEALTH_CHECK=$(curl -s ${SERVICE_URL}/health)

if echo ${HEALTH_CHECK} | grep -q "healthy"; then
    echo -e "${GREEN}✅ Health check passed${NC}"
    echo "Response: $HEALTH_CHECK"
else
    echo -e "${YELLOW}⚠️  Health check pending...${NC}"
fi

# Display endpoints
echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"

echo -e "${BLUE}📚 Available Endpoints:${NC}"
echo "  API Docs:           ${SERVICE_URL}/api/docs"
echo "  Health Check:       ${SERVICE_URL}/health"
echo "  Search Discounts:   ${SERVICE_URL}/search-discounts (POST)"
echo "  All Discounts:      ${SERVICE_URL}/discounts/all (GET)"
echo "  Categories:         ${SERVICE_URL}/discounts/categories (GET)"

echo -e "\n${BLUE}🧪 Test the API:${NC}"
echo -e "  ${YELLOW}curl -X POST ${SERVICE_URL}/search-discounts \\${NC}"
echo -e "    ${YELLOW}-H 'Content-Type: application/json' \\${NC}"
echo -e "    ${YELLOW}-d '{\"query\": \"hotel discounts\"}' ${NC}"

echo -e "\n${BLUE}📊 View Logs:${NC}"
echo -e "  ${YELLOW}gcloud run logs read ${SERVICE_NAME} --limit 100 --follow${NC}"

echo -e "\n${BLUE}🔗 Cloud Console:${NC}"
echo -e "  ${YELLOW}https://console.cloud.google.com/run/detail/${REGION}/${SERVICE_NAME}${NC}"

echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}\n"
