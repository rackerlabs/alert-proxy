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
    _instance = None  # Store the single instance of Config

    def __new__(cls):
        # Implement the Singleton pattern to ensure only one instance of Config
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config() # Load configuration only once
        return cls._instance

    def _load_config(self, filename="config.yaml"):
        """Loads configuration from a YAML file and processes it."""
        try:
            with open(filename, "r") as file:
                config_data = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Error: Configuration file '{filename}' not found.")
            config_data = {}  # Provide an empty dict if file not found
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file '{filename}': {e}")
            config_data = {}

        # Set attributes based on config_data
        for key, value in config_data.items():
            if isinstance(value, dict):
                # For nested dictionaries, create a simple object to hold them
                setattr(self, key, type(key.capitalize(), (object,), value)())
            else:
                setattr(self, key, value)

AlertProxyConfig = Config()

