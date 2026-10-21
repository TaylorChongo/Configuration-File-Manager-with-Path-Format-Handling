"""Configuration File Manager.

Read configuration from JSON, CSV and XML, validate it against ``TypedDict``
schemas, convert between formats and keep versioned backups.
"""

from config_manager.schemas import ConfigDocument, ConfigEntry, ConfigMetadata

__all__ = ["ConfigDocument", "ConfigEntry", "ConfigMetadata"]
__version__ = "0.1.0"
