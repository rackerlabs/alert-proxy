#!/bin/bash
#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/

_OVERRIDES='/etc/genestack/helm-configs/alert-proxy/alert-proxy-overrides.yaml'
pushd /opt/alert-proxy/helm || exit
if test -f $_OVERRIDES; then
  true
else
  mkdir -p "$(dirname $_OVERRIDES)"
  echo '{}' > /etc/genestack/helm-configs/alert-proxy/alert-proxy-overrides.yaml
fi

helm upgrade --install alert-proxy ./ \
    --namespace=alert-proxy \
    --timeout 2m \
    -f $_OVERRIDES \
    --set config.core.account.number="$(kubectl --namespace rackspace get secret alert-proxy -o jsonpath='{.data.core_account_number}' | base64 -d)" \
    --set oversser_core_device_id="$(kubectl --namespace alert-proxy get secret alert-proxy -o jsonpath='{.data.oversser_core_device_id}' | base64 -d)" \
    --set alert_manager_base_url="$(kubectl --namespace alert-proxy get secret alert-proxy -o jsonpath='{.data.alert_manager_base_url}' | base64 -d)" \
    --set account_service_token="$(kubectl --namespace alert-proxy get secret alert-proxy -o jsonpath='{.data.account_service_token}' | base64 -d)" \

popd || exit

