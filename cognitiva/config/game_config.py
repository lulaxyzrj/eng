"""
Game configuration management.
Centralized configuration using Singleton pattern.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional
from pathlib import Path
import json
import os


@dataclass
class GameConfiguration:
    """Complete game configuration."""

    # Application settings
    app_name: str = "Cognitive Memory Game"
    version: str = "1.0.0"
    language: str = "en"

    # Paths
    data_path: str = "./data"
    content_path: str = "./assets"
    theme_path: str = "./assets/themes"
    sound_path: str = "./assets/sounds"

    # Display settings
    window_width: int = 1920
    window_height: int = 1080
    fullscreen: bool = False
    fps_target: int = 60

    # Audio settings
    master_volume: float = 1.0
    music_volume: float = 0.7
    sfx_volume: float = 0.8
    enable_audio: bool = True

    # Game defaults
    default_difficulty: str = "medium"
    enable_animations: bool = True
    animation_speed: float = 1.0
    enable_hints: bool = True
    auto_save: bool = True

    # Accessibility
    enable_screen_reader: bool = False
    high_contrast_mode: bool = False
    large_text_mode: bool = False
    reduce_motion: bool = False
    colorblind_mode: Optional[str] = None

    # Performance
    enable_vsync: bool = True
    texture_quality: str = "high"  # low, medium, high
    enable_shadows: bool = True
    enable_particles: bool = True

    # Privacy and data
    enable_analytics: bool = True
    enable_telemetry: bool = False
    data_retention_days: int = 365

    # AR/VR settings
    vr_enabled: bool = False
    ar_enabled: bool = False
    spatial_audio: bool = False

    # Development
    debug_mode: bool = False
    show_fps: bool = False
    enable_logging: bool = True
    log_level: str = "INFO"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameConfiguration':
        """Create from dictionary."""
        # Filter out unknown keys
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered_data)

    def validate(self) -> bool:
        """Validate configuration values."""
        # Validate volumes
        if not 0.0 <= self.master_volume <= 1.0:
            return False
        if not 0.0 <= self.music_volume <= 1.0:
            return False
        if not 0.0 <= self.sfx_volume <= 1.0:
            return False

        # Validate screen dimensions
        if self.window_width < 800 or self.window_height < 600:
            return False

        # Validate FPS
        if self.fps_target < 30 or self.fps_target > 240:
            return False

        return True

    def apply_accessibility_preset(self, preset: str) -> None:
        """
        Apply an accessibility preset.

        Args:
            preset: 'visual_impairment', 'motor_impairment', 'cognitive_impairment'
        """
        if preset == 'visual_impairment':
            self.high_contrast_mode = True
            self.large_text_mode = True
            self.enable_screen_reader = True
            self.enable_audio = True
            self.sfx_volume = 1.0

        elif preset == 'motor_impairment':
            self.animation_speed = 0.5  # Slower animations
            self.enable_hints = True
            # Longer timeout for interactions (would be handled elsewhere)

        elif preset == 'cognitive_impairment':
            self.default_difficulty = "easy"
            self.enable_hints = True
            self.animation_speed = 0.7
            self.reduce_motion = True


class ConfigurationManager:
    """
    Manages game configuration.
    Singleton pattern.
    """

    _instance: Optional['ConfigurationManager'] = None
    _config: Optional[GameConfiguration] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigurationManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = GameConfiguration()
            self._config_file = "config.json"

    @property
    def config(self) -> GameConfiguration:
        """Get current configuration."""
        if self._config is None:
            self._config = GameConfiguration()
        return self._config

    def load_config(self, file_path: Optional[str] = None) -> bool:
        """
        Load configuration from file.

        Args:
            file_path: Path to config file (default: config.json)

        Returns:
            True if successful
        """
        config_path = file_path or self._config_file

        try:
            if not Path(config_path).exists():
                # Create default config
                self.save_config(config_path)
                return True

            with open(config_path, 'r') as f:
                data = json.load(f)

            self._config = GameConfiguration.from_dict(data)

            if not self._config.validate():
                print("Warning: Invalid configuration values detected")
                return False

            return True

        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    def save_config(self, file_path: Optional[str] = None) -> bool:
        """
        Save configuration to file.

        Args:
            file_path: Path to config file (default: config.json)

        Returns:
            True if successful
        """
        config_path = file_path or self._config_file

        try:
            if self._config is None:
                return False

            with open(config_path, 'w') as f:
                json.dump(self._config.to_dict(), f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def update_setting(self, key: str, value: Any) -> bool:
        """
        Update a single configuration setting.

        Args:
            key: Configuration key
            value: New value

        Returns:
            True if successful
        """
        if self._config is None:
            return False

        if not hasattr(self._config, key):
            return False

        try:
            setattr(self._config, key, value)

            # Validate after update
            if not self._config.validate():
                print(f"Warning: Setting {key}={value} resulted in invalid configuration")

            return True

        except Exception as e:
            print(f"Error updating setting: {e}")
            return False

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration setting.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        if self._config is None:
            return default

        return getattr(self._config, key, default)

    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self._config = GameConfiguration()

    def apply_environment_overrides(self) -> None:
        """Apply configuration overrides from environment variables."""
        # Check for environment variable overrides
        prefix = "MEMORY_GAME_"

        for key in GameConfiguration.__dataclass_fields__.keys():
            env_key = f"{prefix}{key.upper()}"
            if env_key in os.environ:
                value = os.environ[env_key]

                # Type conversion
                field_type = type(getattr(self._config, key))

                try:
                    if field_type == bool:
                        value = value.lower() in ('true', '1', 'yes')
                    elif field_type == int:
                        value = int(value)
                    elif field_type == float:
                        value = float(value)

                    self.update_setting(key, value)

                except ValueError:
                    print(f"Warning: Invalid environment variable value for {env_key}")

    def get_theme_config(self) -> Dict[str, str]:
        """Get theme-related configuration."""
        return {
            'theme_path': self.config.theme_path,
            'high_contrast': str(self.config.high_contrast_mode),
            'colorblind_mode': self.config.colorblind_mode or 'none'
        }

    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio-related configuration."""
        return {
            'master_volume': self.config.master_volume,
            'music_volume': self.config.music_volume,
            'sfx_volume': self.config.sfx_volume,
            'enable_audio': self.config.enable_audio,
            'spatial_audio': self.config.spatial_audio
        }

    def get_display_config(self) -> Dict[str, Any]:
        """Get display-related configuration."""
        return {
            'width': self.config.window_width,
            'height': self.config.window_height,
            'fullscreen': self.config.fullscreen,
            'fps_target': self.config.fps_target,
            'vsync': self.config.enable_vsync
        }
