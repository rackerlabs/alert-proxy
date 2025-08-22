#   ___  _           _  ______
#  / _ \| |         | | | ___ \
# / /_\ \ | ___ _ __| |_| |_/ / __ _____  ___   _
# |  _  | |/ _ \ '__| __|  __/ '__/ _ \ \/ / | | |
# | | | | |  __/ |  | |_| |  | | | (_) >  <| |_| |
# \_| |_/_|\___|_|   \__\_|  |_|  \___/_/\_\\__, |
#                    Alert-Proxy             __/ |
#                                           |___/
import os
import pathlib
import sys
import pytest

# Add the 'src' directory to the Python path to allow imports from it
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))
yaml = pytest.importorskip("yaml")

from config.config import Config


def test_env_substitution(monkeypatch):
    """
    Test environment variable substitution using a real config file.
    """
    # Construct the path to the sample file relative to the 'tests' directory.
    # The path from 'tests' is '../src/config/config.yaml.sample'.
    config_file_path = (
        pathlib.Path(__file__).resolve().parent.parent
        / "src"
        / "config"
        / "config.yaml.sample"
    )

    print(f"config_file_path: {config_file_path}")
    # Set environment variables for substitution
    monkeypatch.setenv("CORE_ACCOUNT_NUMBER", "123456")
    monkeypatch.setenv("OVERSEER_CORE_DEVICE_ID", "654321")
    monkeypatch.setenv("ACCOUNT_SERVICE_TOKEN", "1111-2222-3333-4444")
    monkeypatch.setenv("ALERT_MANAGER_BASE_URL", "https://this.is.a.url")

    # Reset the Singleton to ensure a fresh instance
    Config._instance = None
    cfg = Config()

    # Load configuration from the specified file
    cfg._load_config(str(config_file_path))

    # Assertions to validate environment variable substitution
    assert cfg.alert_proxy_config.core_account_id == "123456"
    assert cfg.alert_proxy_config.core_overseer_id == "654321"
    assert cfg.alert_proxy_config.account_secret == "1111-2222-3333-4444"
    assert cfg.alert_proxy_config.am_v2_base_url == "https://this.is.a.url"
