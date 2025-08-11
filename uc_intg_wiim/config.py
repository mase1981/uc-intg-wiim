"""
Configuration management for WiiM Integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MIT, see LICENSE for more details.
"""

import json
import logging
import os
from typing import Any, Dict, Optional

_LOG = logging.getLogger(__name__)


class Config:
    """Configuration manager for WiiM integration."""

    def __init__(self):
        """Initialize configuration."""
        self._config_dir = os.getenv("UC_CONFIG_HOME", os.path.join(os.getcwd(), "config"))
        self._config_file = os.path.join(self._config_dir, "config.json")
        self._config: Dict[str, Any] = {}
        
        os.makedirs(self._config_dir, exist_ok=True)
        _LOG.info("Configuration directory: %s", self._config_dir)

    def load(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                _LOG.info("Configuration loaded successfully")
            else:
                _LOG.info("No configuration file found, using defaults")
                self._config = {}
        except Exception as e:
            _LOG.error("Error loading configuration: %s", e)
            self._config = {}

    def save(self):
        """Save configuration to file."""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2)
            _LOG.info("Configuration saved successfully")
        except Exception as e:
            _LOG.error("Error saving configuration: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self._config[key] = value

    def update(self, values: Dict[str, Any]):
        """Update multiple configuration values."""
        self._config.update(values)

    def is_configured(self) -> bool:
        """Check if integration is configured."""
        return bool(self._config.get("host"))

    def get_host(self) -> Optional[str]:
        """Get configured WiiM device host."""
        return self._config.get("host")