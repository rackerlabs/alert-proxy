#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
from flask import request, has_request_context
from config.config import Config
import logging
import os
from logging.handlers import RotatingFileHandler

class RequestFormatter(logging.Formatter):
    def format(self, record):
        record.request_id = 'NA'

        if has_request_context():
            record.request_id = request.environ.get("HTTP_X_REQUEST_ID")

        return super().format(record)

class AppLogger:
    def __init__(self, app, log_file=Config.LOG_FILE_NAME,
                 log_dir=Config.LOG_DIR, level=Config.LOG_LEVEL):
        self.logger = logging.getLogger(app)
        self.logger.setLevel(level)

        # Create a file handler
        file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        file_handler.setLevel(level)

        # Create a formatter
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        if not self.logger.handlers: # Prevent adding multiple handlers on reloads
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger

class AlertProxyLogger:
    def __init__(self, app, log_file=Config.LOG_FILE_NAME,
                 log_dir=Config.LOG_DIR, level=Config.LOG_LEVEL):
        #self.logger = logging.getLogger(name)
        self.logger = logging.getLogger('flask_app_logger')
        self.logger.setLevel(level)
        # Construct the full log file path
        log_path = os.path.join(log_dir, log_file)
        # Create the log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        # Use the combined log path for the RotatingFileHandler
        file_handler = RotatingFileHandler(log_path, maxBytes=1024 * 1024 * 5, backupCount=5)
        # Create a formatter and add it to the handler
        formatter = RequestFormatter(
            '[%(asctime)s] [%(levelname)s] [%(request_id)s] %(module)s: %(message)s'
        )
        file_handler.setFormatter(formatter)

        if not self.logger.handlers: # Prevent adding multiple handlers on reloads
            self.logger.addHandler(file_handler)

    def get_logger(self):
        return self.logger
