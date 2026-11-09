#!/usr/bin/env bash
# ==============================================================================
# Enterprise AI Document Assistant - Azure Container Apps Automated Deployment
# ==============================================================================
set -euo pipefail

# Configuration Defaults
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-enterprise-rag}"
LOCATION="${LOCATION:-eastus}"
ENVIRONMENT_NAME="${ENVIRONMENT_NAME:-rag-env}"
ACR_NAME="${ACR_NAME:-acrrag$RANDOM}"
BACKEND_APP_NAME="${BACKEND_APP_NAME:-rag-backend-app}"
FRONTEND_APP_NAME="${FRONTEND_APP_NAME:-rag-frontend-app}"

echo "================================================================="
echo " Starting Azure Container Apps Deployment"
echo " Resource Group: ${RESOURCE_GROUP}"
echo " Location:       ${LOCATION}"
echo " ACR Name:       ${ACR_NAME}"
echo "================================================================="

# 1. Verify Azure CLI login
echo "[1/7] Checking Azure CLI authentication..."
az account show > /dev/null 2>&1 || { echo "ERROR: Please run 'az login' first."; exit 1; }

# 2. Register required Azure resource providers
echo "[2/7] Registering Microsoft.App and Microsoft.OperationalInsights..."
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait

# 3. Create Resource Group
echo "[3/7] Creating Resource Group '${RESOURCE_GROUP}' in '${LOCATION}'..."
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}"

# 4. Create Azure Container Registry
echo "[4/7] Creating Azure Container Registry '${ACR_NAME}'..."
az acr create \
  --resource-group "${RESOURCE_GROUP}" \
  --name "${ACR_NAME}" \
  --sku Basic \
  --admin-enabled true

ACR_LOGIN_SERVER=$(az acr show --name "${ACR_NAME}" --query loginServer --output tsv)
ACR_PASSWORD=$(az acr credential show --name "${ACR_NAME}" --query "passwords[0].value" --output tsv)

# 5. Build and Push Container Images using ACR Tasks (cloud build)
echo "[5/7] Building container images in ACR..."
echo "  Building backend image..."
az acr build \
  --registry "${ACR_NAME}" \
  --image "${ACR_LOGIN_SERVER}/rag-backend:latest" \
  --file docker/Dockerfile.backend \
  backend/

echo "  Building frontend image..."
az acr build \
  --registry "${ACR_NAME}" \
  --image "${ACR_LOGIN_SERVER}/rag-frontend:latest" \
  --file docker/Dockerfile.frontend \
  frontend/

# 6. Create Azure Container Apps Environment
echo "[6/7] Creating Container Apps Environment '${ENVIRONMENT_NAME}'..."
az containerapp env create \
  --name "${ENVIRONMENT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}"

# 7. Deploy Backend Container App
echo "[7/7] Deploying Backend Container App..."
az containerapp create \
  --name "${BACKEND_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --environment "${ENVIRONMENT_NAME}" \
  --image "${ACR_LOGIN_SERVER}/rag-backend:latest" \
  --target-port 8000 \
  --ingress external \
  --registry-server "${ACR_LOGIN_SERVER}" \
  --registry-username "${ACR_NAME}" \
  --registry-password "${ACR_PASSWORD}" \
  --env-vars \
    PROJECT_NAME="Enterprise AI Document Assistant" \
    VERSION="1.0.0" \
    OPENAI_API_KEY="secretref:openai-key" \
    OPENAI_MODEL="gpt-4o-mini" \
    EMBEDDING_MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2" \
  --secrets \
    "openai-key=${OPENAI_API_KEY:-dummy-key-replace-in-portal}"

BACKEND_URL=$(az containerapp show --name "${BACKEND_APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query "properties.configuration.ingress.fqdn" --output tsv)

# Deploy Frontend Container App
echo "  Deploying Frontend Container App..."
az containerapp create \
  --name "${FRONTEND_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --environment "${ENVIRONMENT_NAME}" \
  --image "${ACR_LOGIN_SERVER}/rag-frontend:latest" \
  --target-port 80 \
  --ingress external \
  --registry-server "${ACR_LOGIN_SERVER}" \
  --registry-username "${ACR_NAME}" \
  --registry-password "${ACR_PASSWORD}"

FRONTEND_URL=$(az containerapp show --name "${FRONTEND_APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query "properties.configuration.ingress.fqdn" --output tsv)

echo "================================================================="
echo " DEPLOYMENT COMPLETE!"
echo " Backend Live URL:  https://${BACKEND_URL}"
echo " Frontend Live URL: https://${FRONTEND_URL}"
echo " Swagger Docs:     https://${BACKEND_URL}/docs"
echo "================================================================="
