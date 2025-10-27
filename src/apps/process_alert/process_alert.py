#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
from flask.views import MethodView
from flask import Blueprint, request, jsonify, current_app, has_request_context
from config.config import settings
import requests
import json
from apps.process_alert import process_alert_bp


class ProcessAlert(MethodView):
    def _is_alert_still_firing(self, fingerprint=None):
        """
        Query Alert Manager API by fingerprint and confirm status is firing
        Args:
            fingerprint (str): Alert fingerprint to filter on
        """
        alert_status = None
        is_firing = False
        filtered_alerts = []

        current_app.logger.debug(
            f"alert_proxy_config.alert_manager_url: { settings.alert_proxy_config.alert_manager_url }"
        )
        response = requests.get(settings.alert_proxy_config.alert_manager_url)
        current_app.logger.debug(
            f"Response from alert_manager_url: { response.json() }"
        )
        if response.status_code == 200:
            alerts = response.json()
            if not alerts:
                current_app.logger.info(
                    f"No alerts returned by { settings.alert_proxy_config.alert_manager_url }"
                )
                return is_firing
            filtered_alerts = [alert for alert in alerts if alert.get("fingerprint") == fingerprint]
            for alert in filtered_alerts:
                alert_status = alert["status"].get("state", "NONE")
                current_app.logger.info(
                    f"Alertmanater api reports alert with fingerprint { fingerprint } has a status of: { alert_status } "
                )
        else:
            current_app.logger.error(
                f"Failed to retrieve alerts. Status code: {response.status_code}"
            )

        if alert_status == "active":
            is_firing = True
        return is_firing

    def _create_core_ticket(self, url=None, headers=None, payload=None):
        """
        Create a core ticket with payload pulled form the Alert
        Args:
            payload (json): Payload used when posting against the Watchman API
        """
        response = None

        try:
            response = requests.post(url=url, headers=headers, json=payload)
            response.raise_for_status()
            current_app.logger.info("Post to watchman api was successful.")
        except requests.exceptions.HTTPError as e:
            current_app.logger.error(f"Request failed: {e}")

        return response

    def get(self):
        """
        Generic GET endpoint action that will return a 200.
        Designed for Kubernetes liveness and readiness probes.
        """
        current_app.logger.info("Health check GET request accepted.")
        return jsonify({"status": "success", "message": "GET accepted"}), 200

    def post(self):
        """
        HTTP Post to accept Alertmanager Alert
        Args: JSON payload from Alertmanager for processing into a core ticket
        """
        current_app.logger.info(f"BEGIN alert processing......")
        content_type = request.headers.get("Content-Type")

        # set the request-id for inclusion into the core ticket
        request_id = (
            request.environ.get("HTTP_X_REQUEST_ID") if has_request_context() else None
        )

        if content_type == "application/json":
            alert_data = request.get_json(silent=True)
            if not alert_data or not (
                alert_data.get("commonAnnotations") or alert_data.get("commonLabels")
            ):
                current_app.logger.error(f"Invalid or missing json payload")
                current_app.logger.info(f"Value of INVALID data: { alert_data }")
                current_app.logger.info(f"END alert processing......")
                return jsonify({"message": f"Invalid or missing json payload"}), 400
            current_app.logger.debug(
                f"Value of post from alertmanager receiver webhook: { alert_data }"
            )
        else:
            current_app.logger.error(
                f"Invalid of missing Contect-Type of application/json"
            )
            current_app.logger.info(f"END alert processing......")
            return jsonify({"message": "Content-Type is not application/json"}), 400

        # Configure top-level alert variables
        a_name = alert_data["commonLabels"].get("alertname", "NONE")
        a_status = (
            "ALARM"
            if alert_data["status"] == "firing"
            else "OK" if alert_data["status"] == "resolved" else "OK"
        )
        a_subject = alert_data["commonAnnotations"].get("summary", "SUMMARY")
        a_description = alert_data["commonAnnotations"].get(
            "description", "FIXME: DESCRIPTION NOT PROVIDED IN ALERT"
        )
        a_overseerID = alert_data["commonLabels"].get(
            "overseerID", settings.alert_proxy_config.core_overseer_id
        )
        a_coreAccountID = alert_data["commonLabels"].get(
            "coreAccountID", settings.alert_proxy_config.core_account_id
        )
        a_secret = settings.alert_proxy_config.account_secret

        # loop through all alerts contained in the receiver webhook payload
        alerts = alert_data.get("alerts", [])
        current_app.logger.info(
            f"Received alert dump.  Total number of alerts to process: { len(alerts) }"
        )
        count = 0
        for alert in alerts:
            count += 1
            a_fingerprint = alert.get("fingerprint", "UNKNOWN")
            a_severity = alert.get("labels", {}).get("severity", "warning")
            # a_severity = alert.get('severity', 'warning')
            current_app.logger.info(f"Processing { count } of { len(alerts) } ...")
            alert["labels"]["request-id"] = request_id if request_id else "NONE"
            if request_id:
                alert.setdefault("labels", {})["request-id"] = request_id
            current_app.logger.debug(f"Alert { count } payload: { alert }")
            if settings.alert_proxy_config.alert_verification:
                if self._is_alert_still_firing(a_fingerprint):
                    a_alert_still_firing = True
                    current_app.logger.info(
                        f"Alert with fingerprint: { a_fingerprint } is still firing. creating ticket..."
                    )
                else:
                    a_alert_still_firing = False
                    current_app.logger.info(
                        f"Alert with fingerprint: { a_fingerprint } is not active. skipping ticket creation."
                    )
                    continue
            current_app.logger.info(f"Formatting alert for watchman ingestion")
            if a_severity == "warning":
                w_url = f"https://watchman.api.manage.rackspace.com/v1/hybrid:{ a_coreAccountID }/webhook/platformservices?secret={ a_secret }&severity=low"
            else:
                w_url = f"https://watchman.api.manage.rackspace.com/v1/hybrid:{ a_coreAccountID }/webhook/platformservices?secret={ a_secret }&severity=high"
            w_headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            w_body = f"""########## ALERT DETAILS
Name: { a_subject}
Instance: { alert.get('labels', {}).get('instance', 'FIXME: instance not defined.') }
Description: { a_description }
Severity: { a_severity }
Alert Still Firing: { a_alert_still_firing }
Started at: { alert.get('startsAt', 'FIXME: startsAt not defined.') }

########## CONNECTION INFO
coreDeviceID: { alert.get('labels', {}).get('coreDeviceID', 'UNKNOWN') }
coreAccountID: { a_coreAccountID }
overseerID: { a_overseerID }

########## LINKS
Suppression Link: { settings.alert_proxy_config.alert_manager_url }/#/alerts?filter=%7Balertname%3D%22{ a_name }%22%2C%20rackspace_com_coreAccountID%3D%22{ a_coreAccountID }%22%2C%20rackspace_com_overseerID%3D%22{ a_overseerID }%22%2C%20severity%3D%22{ a_severity }%22%7D
Grafana: grafana.{ settings.alert_proxy_config.http_route_fqdn }
Alertmanager: alertmanager.{ settings.alert_proxy_config.http_route_fqdn }
Prometheus: prometheus.{ settings.alert_proxy_config.http_route_fqdn }

########## ALERT-PROXY INFO
Request-ID: { alert.get('labels', {}).get('request-id', 'FIXME: request-id not defined.') }
"""
            w_payload = {
                "subject": f"[ALERT-PROXY] { a_subject }",
                "body": w_body,
                "privateComment": "\n".join(
                    [f"{x}: {v}" for x, v in alert.get("labels").items()]
                ),
                "alarmState": a_status,
                "threadId": f"{ a_coreAccountID }-{ a_fingerprint }",
                "sender": "alert-proxy",
            }
            # post the payload against watchman
            try:
                current_app.logger.debug(f"w_url: { w_url }")
                current_app.logger.debug(f"w_headers: { w_headers }")
                current_app.logger.debug(f"w_body: { w_body }")
                current_app.logger.debug(f"w_payload: { w_payload }")
                if settings.alert_proxy_config.create_ticket:
                    response = self._create_core_ticket(w_url, w_headers, w_payload)
            except Exception as e:
                current_app.logger.error(f"Uncaught error: {str(e)}")
                continue
        current_app.logger.info(f"END alert processing...")
        return jsonify({"message": f"success: true"}), 201


process_alert_bp.add_url_rule(
    "/process", view_func=ProcessAlert.as_view("alert_api"), strict_slashes=False
)
