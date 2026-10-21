from pathlib import Path

import pytest

from config_manager.schemas import ConfigDocument

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_ROOT / "samples"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def samples_dir() -> Path:
    return SAMPLES_DIR


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def sample_document() -> ConfigDocument:
    """In-memory equivalent of samples/app_config.*"""
    return {
        "metadata": {
            "name": "app",
            "version": "1.0.0",
            "description": "Sample application configuration",
        },
        "entries": [
            {"section": "database", "key": "host", "value": "localhost", "type": "str",
             "description": "Database host"},
            {"section": "database", "key": "port", "value": 5432, "type": "int",
             "description": "Database port"},
            {"section": "database", "key": "pool_timeout", "value": 30.5, "type": "float"},
            {"section": "server", "key": "debug", "value": False, "type": "bool",
             "description": "Enable debug mode"},
            {"section": "server", "key": "workers", "value": 4, "type": "int"},
            {"section": "logging", "key": "level", "value": "INFO", "type": "str"},
        ],
    }
