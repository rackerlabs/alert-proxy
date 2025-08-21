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
#, has_request_context
from config.config import settings
import requests
import json
from apps.process_alert import process_alert_bp


class ProcessAlert(MethodView):
    def _is_alert_still_firing(self, fingerprint=None):
        """
        Query Alert Manager API by fingerprint and confirm status is firing
        Args:
            fingerprint (str): Alert fingercurrent_app.logger.debug to filter on
        """
        alert_status = None
        is_firing = False

        response = requests.get(settings.alert_proxy_config.am_v2_base_url)

        if response.status_code == 200:
            alerts = response.json()
            if not alerts:
                current_app.logger.info(f"No alerts returned by { settings.alert_proxy_config.am_v2_base_url }")
                return is_firing
            for alert in alerts:
                if alert['fingerprint'] == fingerprint:
                    alert_status=alert['status'].get('state')
                    current_app.logger.info(f"Alertmanater api reports alert with fingerprint { fingerprint } has a status of: { alert_status } ")
        else:
            current_app.logger.error(f"Failed to retrieve alerts. Status code: {response.status_code}")

        if alert_status == 'active':
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
        Generic get endpoint action that will return a 200.  For use with liveness probes
        Args: NONE
        """
        current_app.logger.info("GET request accepted")
        return_payload = {"status": "success", "message": "GET accepted"}
        return jsonify(return_payload), 200

    def post(self):
        """
        HTTP Post to accept Alertmanager Alert
        Args: JSON payload from Alertmanager for processing into a core ticket
        """
        current_app.logger.info(f"BEGIN alert processing......")
        content_type = request.headers.get('Content-Type')

        # set the request-id for inclusion into the core ticket
        if has_request_context():
            request_id = request.environ.get("HTTP_X_REQUEST_ID")

        if content_type == 'application/json':
            alert_data = request.get_json(silent=True)
            if not alert_data or not (alert_data.get('commonAnnotations') or
                                       alert_data.get('commonLabels')):
                current_app.logger.error(f"Invalid or missing json payload")
                current_app.logger.info(f"Value of INVALID data: { alert_data }")
                current_app.logger.info(f"END alert processing......")
                return jsonify({"message": f"Invalid or missing json payload"}), 400
            current_app.logger.debug(f"Value of post from alertmanager webhook: { alert_data }")
        else:
            current_app.logger.error(f"Invalid of missing Contect-Type of application/json")
            current_app.logger.info(f"END alert processing......")
            return jsonify({"message": "Content-Type is not application/json"}), 400

        # set the request-id for inclusion into the core ticket
        if has_request_context():
            request_id = request.environ.get("HTTP_X_REQUEST_ID")

        # set some values or defaults if not defined
        a_name = alert_data['commonLabels'].get('alertname', "NONE")
        a_status = "ALARM" if alert_data['status'] == "firing" else "OK" if alert_data['status'] == "resolved" else "OK"
        a_subject = alert_data['commonAnnotations'].get('summary', 'SUMMARY')
        a_description = alert_data['commonAnnotations'].get('description', 'DESCRIPTION')
        a_oversserID = alert_data['commonLabels'].get('oversserID', settings.alert_proxy_config.core_overseer_id)
        a_coreAccountID = alert_data['commonLabels'].get('coreAccountID', settings.alert_proxy_config.account_secret)
        a_secret = settings.alert_proxy_config.account_secret


        alerts = alert_data.get('alerts', [])
        current_app.logger.info(f"Received alert dump.  Total number of alerts to process: { len(alerts) }")
        count = 0;
        for alert in alerts:
            count += 1
            a_fingerprint = alert.get('fingerprint','UNKNOWN')
            a_severity = alert.get('severity', 'warning')
            current_app.logger.info(f"Processing { count } of { len(alerts) } ...")
            alert['labels']['request-id'] = request_id
            current_app.logger.debug(f"Alert { count } payload: { alert }")
            if settings.alert_proxy_config.alert_verification:
                if self._is_alert_still_firing(a_fingerprint):
                    current_app.logger.info(f"Alert with fingerprint: { a_fingerprint } is still firing. creating ticket...")
                else:
                    current_app.logger.info(f"Alert with fingerprint: { a_fingerprint } is not active. skipping ticket creation.")
                    continue
            current_app.logger.info(f"Formatting alert for watchman ingestion")
            if a_severity == "warning":
                w_url = f"https://watchman.api.manage.rackspace.com/v1/hybrid:{ a_coreAccountID }/webhook/platformservices?secret={ a_secret }&severity=low"
            else:
                w_url = f"https://watchman.api.manage.rackspace.com/v1/hybrid:{ a_coreAccountID }/webhook/platformservices?secret={ a_secret }&severity=high"
            w_headers = {
                    "Accept": "application/json",
                    "Content-Type": "application/json"
            }
            w_body = f"""Severity: { a_severity }
Instance: { alert.get('labels', {}).get('instance','UNKNOWN') }
coreDeviceID: { alert.get('coreDeviceID', 'UNKNWON') }
coreAccountID: { a_coreAccountID }
overseerID: { a_overseerID }
Description: { a_description }
Started at: { alert.get('startsAt','UNKNOWN') }
Suppression Link: { settings.alert_proxy_config.am_v2_base_url }/#/alerts?filter=%7Balertname%3D%22{ a_name }%22%2C%20rackspace_com_coreAccountID%3D%22{ a_coreAccountID }%22%2C%20rackspace_com_overseerID%3D%22{ a_overseerID }%22%2C%20severity%3D%22{ a_severity }%22%7D
"""
            w_payload = {
                "subject": f"ALERT-PROXY-{ a_subject }",
                "body": w_body,
                "privateComment": "\n".join([f"{x}:{v}" for x, v in alert.get('labels').items()]),
                "alarmState": a_status,
                "threadId": f"{ a_coreAccountID }-{ a_fingerprint }",
                "sender": "alert-proxy"
            }
            # post the payload against watchman
            try:
                response = self._create_core_ticket(w_url, w_headers, w_payload)
#                current_app.logger.debug(f"RESPONSE: { response }")
            except Exception as e:
                current_app.logger.error(f"Uncaught error: {str(e)}")
                continue
        current_app.logger.info(f"END alert processing...")
        return jsonify({"message": f"success: true"}), 201

process_alert_bp.add_url_rule('/process', view_func=ProcessAlert.as_view('alert_api'), strict_slashes=False)
