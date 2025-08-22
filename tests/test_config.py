import os
import pathlib
import sys
import pytest

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
yaml = pytest.importorskip('yaml')

from config.config import Config


def test_env_substitution(tmp_path, monkeypatch):
    data = {
        'secret': '${TEST_SECRET}',
        'nested': {'value': '${TEST_NESTED}'}
    }
    config_file = tmp_path / 'config.yaml'
    config_file.write_text(yaml.dump(data))
    monkeypatch.setenv('TEST_SECRET', 'hello')
    monkeypatch.setenv('TEST_NESTED', 'world')
    Config._instance = None
    cfg = Config()
    cfg._load_config(str(config_file))
    assert cfg.secret == 'hello'
    assert cfg.nested.value == 'world'
