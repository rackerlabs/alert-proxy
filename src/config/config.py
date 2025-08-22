#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
import yaml
import os

class Config:
    _instance = None
    _initialized = False

    def __new__(cls, filename="config.yaml"):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self, filename="config.yaml"):
        if not self._initialized:
            self._load_config(filename)
            Config._initialized = True

    def _resolve_env(self, value):
        if isinstance(value, str):
            return os.path.expandvars(value)
        if isinstance(value, dict):
            return {k: self._resolve_env(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_env(v) for v in value]
        return value

    def _load_config(self, filename):
        try:
            with open(filename, "r") as file:
                config_data = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Error: Configuration file '{filename}' not found.")
            config_data = {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file '{filename}': {e}")
            config_data = {}

        processed_data = self._resolve_env(config_data)

        for key, value in processed_data.items():
            if isinstance(value, dict):
                setattr(self, key, type(key.capitalize(), (object,), value)())
            else:
                setattr(self, key, value)

# This line reads the specified file
settings = Config("/etc/alert-proxy/config.yaml")

