Alert-Proxy Installation and Configuration

This guide outlines the steps to configure and deploy the alert-proxy service, split into steps performed on your local workstation and steps performed on the overseer/deployment node.

Part 1: From Your Local Workstation

These steps gather necessary credentials and configuration details.

1. Determine and Export the Core Account ID

Determine the core account ID and export it as an environment variable named ACCOUNT.

Command:

``` shell
export ACCOUNT=<core_account_id>
```

2. Get a Racker Token

Obtain a Racker token using the ht credentials command.

Command:

``` shell
(ht) ➜ ~ ht credentials
```

Sample Response:

<TOKEN>

3. Create the TOKEN Environment Variable

Export the retrieved token as an environment variable named TOKEN.

Command:

``` shell
export TOKEN=<token>
```

4. Get the Webhooks Secret Key

Use curl against the Watchman API to retrieve the webhooks configuration and specifically grab the secret key from the returned JSON payload.

Command:

```shell
curl -H "X-Auth-Token: $TOKEN" -H "X-Tenant-Id: dedicated:$ACCOUNT" \
  https://watchman.api.manage.rackspace.com/v1/hybrid:$ACCOUNT/webhooks
```
Sample Response (partial):

``` json
{"webhooks":[{"severity":"low","rel":"webhook-datadog-low","href":"/v1/hybrid:5915600/webhook/datadog?secret=<account_secret>&severity=low","name":"Datadog","enabled":true} …
```
    NOTE: The value of <account_secret> is the Account Service Token needed in Step 9.

5. Determine the Alertproxy URL

Determine the Alertmanager UI frontend HTTP route (the alertproxy URL) for the environment where you are deploying alert-proxy.

For flex environments, the format is typically:
http://kube-prometheus-stack-alertmanager.prometheus.svc.cluster.local:9093/api/v2/alerts

    NOTE: This URL must be accessible from the container network. It is used to validate that an alert is still firing before creating a ticket in core. To disable this function, set alert_verification: true to false in the /etc/genestack/helm-configs/alert-proxy/ configuration:

```yaml
    alert_proxy_config:
      alert_verification: true # Change to false to disable verification
```

6. Determine the HTTP_ROUTE_FQDN

The HTTP_ROUTE_FQDN secret will be used when applying links into the public comment of the ticket.  In FLEX, we run grafana/prometheus/alertmanger/others at ***cluster***.ohthree.com.  So the HTTP_ROUTE_FQDN should be set to ***cluster***.ohthree.com.  For environments NOT FLEX, HTTP_ROUTE_FQDN should be set to the base fqdn used for accessing the cluster. 

Part 2: From the Overseer / Deployment Node

These steps involve preparing the environment and deploying the alert-proxy.


7. Git Clone the Repository

Clone the alert-proxy repository to the deployment/overseer node.

Commands:

``` shell
cd /opt/alert-proxy
git clone git@github.com-alert-proxy:rackerlabs/alert-proxy.git .
```

8. Create Alert-Proxy Secrets

Run the create_secrets.sh script and answer the prompts using the information gathered in Steps 1-3.

    NOTE: The Account Service Token is the secret key found in Step 4.

Commands:

``` shell
cd /opt/alert-proxy/bin
./create_secrets.sh
```

Expected Outcome:

Creating Kubernetes Secrets...
secret/core-account-id-secret created
secret/overseer-core-device-id-secret created
secret/account-service-token-secret created
secret/alert-manager-base-url-secret created
secret/http-route-fqdn-secret created
All secrets have been created in the 'rackspace' namespace.

9. Create Alert-Proxy Helm Overrides

Create the alert-proxy-overrides.yaml file in the /etc/genestack/helm-configs/alert-proxy/ directory.

Commands:

``` shell
cd /etc/genestack/helm-configs
mkdir alert-proxy
cd alert-proxy

cat <<EOF > alert-proxy-overrides.yaml
---
image:
  tag: "1758659725"

config:
  logging:
    log_level: "DEBUG"
  alert_proxy_config:
    alert_verification: true
    create_ticket: false
EOF
```

10. Update Alertmanager Configuration

Edit the Alertmanager configuration file to include a new webhook route and receiver for the alert-proxy.

Command:

``` shell
vi /etc/genestack/helm-configs/kube-prometheus-stack/alertmanager_config.yaml
```

Route Section

Find the route section and add the following:

``` yaml
        - receiver: 'alert_proxy_receiver'
          continue: true
          matchers:
            - severity =~ "critical"
```
    NOTE: continue: true is only needed if there are additional routes after the alert-proxy section.

Receivers Section

Navigate to the receivers section and add the following:

``` yaml
      - name: 'alert_proxy_receiver'
        webhook_configs:
          - url: 'http://alert-proxy.rackspace.svc.cluster.local/alert/process'
            send_resolved: false
```

11. Install Alert-Proxy

Install or upgrade alert-proxy using the installation script.

Command:

``` shell
/opt/alert-proxy/bin/install-alert-proxy.sh
```

Expected Outcome:

``` shell
Attempting to install/upgrade alert-proxy Helm chart in namespace: rackspace
Release "alert-proxy" does not exist. Installing it now.
NAME: alert-proxy
LAST DEPLOYED: Mon Sep 15 14:43:49 2025
NAMESPACE: rackspace
STATUS: deployed
REVISION: 1
TEST SUITE: None

/opt
Helm upgrade/install process completed.
```

12. Verify Pod Status

Verify that the alert-proxy pod is running as expected in the rackspace namespace.

Command:

``` shell
kubectl get all -n rackspace
```

13. Reinstall Prometheus

Finally, reinstall Prometheus to apply the Alertmanager updates.

Command:

```shell
/opt/genestack/bin/install-kube-prometheus-stack.sh
```

14. View Alert-Proxy Logs

View the alert-proxy logs to monitor its operation. Replace <pod_uuid> with the actual pod ID.

Command:

``` shell
kubectl -n rackspace logs alert-proxy-deployment-<pod_uuid> -f
```

Troubleshooting

1. Validate Alertmanager API Reachability

Validate that the alert-proxy pod can reach the Alertmanager API endpoint.

Command:

``` shell
kubectl -n rackspace exec alert-proxy-deployment-<pod_uuid> -- curl http://kube-prometheus-stack-alertmanager.prometheus.svc.cluster.local:9093/api/v2/alerts
```

Expected Output:
A long list of currently firing alerts, if any.

Example Output (partial):

``` json
[{"annotations":{"description":"32.56% throttling of CPU in namespace kube-system for container openvswitch in pod ovs-ovn-885mv on cluster .","runbook_url":"https://runbooks.prometheus-operator.dev/runbooks/kubernetes/cputhrottlinghigh","summary":"Processes experience elevated CPU throttling."},"endsAt":"2025-10-15T17:29:44.690Z","fingerprint":"031d4170c36bfc71","receivers":
[{"name":"msteams_config"}],"startsAt":"2025-10-15T08:39:14.690Z","status":{"inhibitedBy":["c6099174b6ae400f"],"silencedBy":[] …
```
