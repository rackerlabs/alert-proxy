#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
from flask import request, has_request_context
from config.config import AlertProxyConfig
import logging
import os

class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.request_id = 'NA'

        if has_request_context():
            record.request_id = request.environ.get("HTTP_X_REQUEST_ID")

        return super().format(record)

class AlertProxyLogger:
    def __init__(self, app):
        self.app = app
        # Construct the full log file path
        self.log_dir = AlertProxyConfig.LOG_DIR
        self.log_file = AlertProxyConfig.LOG_FILE_NAME
        self.level = AlertProxyConfig.LOG_LEVEL
        self.log_path = os.path.join(self.log_dir, self.log_file)
        self._configure_logger()

    def _configure_logger(self):
        # Create the log directory if it doesn't exist
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Set the level for the Flask app's logger
        self.app.logger.setLevel(self.level)

        # Create a file handler
        file_handler = logging.FileHandler(self.log_path)
        file_handler.setLevel(self.level)
        stream_handler = logging.StreamHandler()        

        # Create a formatter
        formatter = RequestFormatter(
            '[%(asctime)s] [%(levelname)s] [%(request_id)s] %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        # Add the file handler to the app's logger
        self.app.logger.addHandler(file_handler)
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

