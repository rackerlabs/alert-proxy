#!/bin/bash
#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
NAMESPACE="rackspace"

# Ensure the namespace exists
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

read -rp "Core Account Number: " CORE_ACCOUNT_NUMBER
read -rp "Overseer Core Device ID: " OVERSEER_CORE_DEVICE_ID
read -rp "Account Service Token: " ACCOUNT_SERVICE_TOKEN
read -rp "Alert Manager Base URL: " ALERT_MANAGER_BASE_URL
read -rp "Base URL: " HTTP_ROUTE_FQDN

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

# Create accountServiceToken-secret
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  # CORRECTED: Name must be all lowercase as per RFC 1123 and values.yaml
  name: account-service-token-secret
  namespace: $NAMESPACE
type: Opaque
data:
  account_service_token: $(echo -n "$ACCOUNT_SERVICE_TOKEN" | base64 -w0)
EOF

# Create alertManagerBaseUrl-secret
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: alert-manager-base-url-secret
  namespace: $NAMESPACE
type: Opaque
data:
  alert_manager_base_url: $(echo -n "$ALERT_MANAGER_BASE_URL" | base64 -w0)
EOF

# Create http_route_fqdn
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: http-route-fqdn-secret
  namespace: $NAMESPACE
type: Opaque
data:
  http_route_fqdn: $(echo -n "$HTTP_ROUTE_FQDN" | base64 -w0)
EOF
echo "All secrets have been created in the '$NAMESPACE' namespace."
