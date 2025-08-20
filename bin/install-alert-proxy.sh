#!/bin/bash
#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
#!/bin/bash
#!/bin/bash
# ... (header comments) ...

# Define the namespace for consistency with values.yaml
HELM_NAMESPACE="rackspace"

# Define the path for overrides file
OVERRIDES_FILE='/etc/genestack/helm-configs/alert-proxy/alert-proxy-overrides.yaml'

# Push current directory, navigate to chart root, or exit on failure
pushd /opt/alert-proxy/helm || exit

# Create the overrides directory and an empty overrides file if it doesn't exist
if [[ ! -f "$OVERRIDES_FILE" ]]; then
  echo "Overrides file not found. Creating empty file at $OVERRIDES_FILE"
  mkdir -p "$(dirname "$OVERRIDES_FILE")"
  echo '{}' > "$OVERRIDES_FILE"
fi

echo "Attempting to install/upgrade alert-proxy Helm chart in namespace: $HELM_NAMESPACE"

helm upgrade --install alert-proxy ./ \
    --namespace "$HELM_NAMESPACE" \
    --timeout 2m \
    -f "$OVERRIDES_FILE"

# Pop back to the original directory, or exit on failure
popd || exit

echo "Helm upgrade/install process completed."
