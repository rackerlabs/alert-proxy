#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-need-a-very-secret-key-here' #
    DEBUG = False
    TESTING = False

    # Session management
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600

    # Logging
    LOG_LEVEL = 'INFO'
    LOG_DIR = 'logs'
    LOG_FILE_NAME = 'alert_proxy.log'

class AlertProxyConfig(Config):
    APP_DEBUG = False
    LOG_LEVEL = 'DEBUG'
    ALERT_VERIFICATION = False
    CORE_ACCOUNT_ID = "935811"
    CORE_OVERSEER_ID = "5002029"
    ACCOUNT_SECRET = "e752bde87816b3b9778b98b21608a45b7bbbfe0a02f2449058372c5732bd2a61"
    CLUSTER_REGION = os.environ.get('CLUSTER_REGION', 'dev.dfw')
    AM_V2_BASE_URL = f"https://alertmanager.{ CLUSTER_REGION }.ohthree.com/api/v2/alerts"
