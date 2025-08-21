#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
from flask import request, has_request_context
from config.config import settings
import logging
import sys

class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.request_id = 'NA'

        if has_request_context():
            record.request_id = request.environ.get("HTTP_X_REQUEST_ID")

        return super().format(record)

class AlertProxyLogger:
    def __init__(self, app):
        self.app = app
        self.level = settings.logging.log_level
        self._configure_logger()

    def _configure_logger(self):
        # Remove all existing handlers from the app logger
        while self.app.logger.hasHandlers():
            self.app.logger.removeHandler(self.app.logger.handlers[0])

        # Set the level for the Flask app's logger
        self.app.logger.setLevel(self.level)

        # Create a stream handler to log to stdout
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(self.level)

        # Create a formatter
        formatter = RequestFormatter(
            '[%(asctime)s] [%(levelname)s] [%(request_id)s] %(module)s: %(message)s'
        )
        stream_handler.setFormatter(formatter)

        # Add the stream handler to the app's logger
        self.app.logger.addHandler(stream_handler)
        self.app.logger.propagate = False

    def debug(self, message, *args, **kwargs):
        self.app.logger.debug(message, *args, **kwargs)

    def info(self, message, *args, **kwargs):
        self.app.logger.info(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self.app.logger.warning(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self.app.logger.error(message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self.app.logger.critical(message, *args, **kwargs)
