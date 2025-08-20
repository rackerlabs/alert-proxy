#!/bin/bash

# This script creates individual Kubernetes Secrets for each sensitive value,
# matching the format expected by the Helm chart's values.yaml.

NAMESPACE="rackspace"

# Ensure the namespace exists
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

read -rp "Core Account Number: " CORE_ACCOUNT_NUMBER
read -rp "Overseer Core Device ID: " OVERSEER_CORE_DEVICE_ID
read -rsp "Account Service Token: " ACCOUNT_SERVICE_TOKEN
echo # Add a newline after the password prompt for cleaner output
read -rp "Alert Manager Base URL: " ALERT_MANAGER_BASE_URL

echo "Creating Kubernetes Secrets..."

# Create core-account-id-secret
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: core-account-id-secret
  namespace: $NAMESPACE
type: Opaque
data:
  core_account_number: $(echo -n "$CORE_ACCOUNT_NUMBER" | base64 -w0)
EOF
echo "Secret 'core-account-id-secret' created."

# Create overseer-core-device-id-secret
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: overseer-core-device-id-secret
  namespace: $NAMESPACE
type: Opaque
data:
  overseer_core_device_id: $(echo -n "$OVERSEER_CORE_DEVICE_ID" | base64 -w0)
EOF
echo "Secret 'overseer-core-device-id-secret' created."

# Create accountServiceToken-secret
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: accountServiceToken-secret
  namespace: $NAMESPACE
type: Opaque
data:
  account_service_token: $(echo -n "$ACCOUNT_SERVICE_TOKEN" | base64 -w0)
EOF
echo "Secret 'accountServiceToken-secret' created."

# Create alertManagerBaseUrl-secret
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: alertManagerBaseUrl-secret
  namespace: $NAMESPACE
type: Opaque
data:
  alert_manager_base_url: $(echo -n "$ALERT_MANAGER_BASE_URL" | base64 -w0)
EOF
echo "Secret 'alertManagerBaseUrl-secret' created."

echo "All secrets have been created in the '$NAMESPACE' namespace."

