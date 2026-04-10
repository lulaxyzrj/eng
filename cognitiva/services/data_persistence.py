"""
Data persistence service for saving and loading game data.
Repository pattern for data storage.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import pickle
from datetime import datetime

from ..models.patient import Patient
from ..models.game_content import ContentItem, GameContent
from ..models.game_state import GameState, GameSession


class DataStore(ABC):
    """
    Abstract base class for data storage.
    Strategy pattern for different storage backends.
    """

    @abstractmethod
    def save(self, key: str, data: Any) -> bool:
        """Save data with a key."""
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """Load data by key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete data by key."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all keys, optionally filtered by prefix."""
        pass


class JSONFileStore(DataStore):
    """
    JSON file-based storage implementation.
    Simple and human-readable storage.
    """

    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key."""
        # Sanitize key to be filesystem-safe
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_path / f"{safe_key}.json"

    def save(self, key: str, data: Any) -> bool:
        """Save data as JSON."""
        try:
            file_path = self._get_file_path(key)

            # Convert to dict if object has to_dict method
            if hasattr(data, 'to_dict'):
                data = data.to_dict()

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            return True
        except Exception as e:
            print(f"Error saving {key}: {e}")
            return False

    def load(self, key: str) -> Optional[Any]:
        """Load data from JSON."""
        try:
            file_path = self._get_file_path(key)

            if not file_path.exists():
                return None

            with open(file_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            print(f"Error loading {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a file."""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if file exists."""
        return self._get_file_path(key).exists()

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all JSON files."""
        keys = []
        for file_path in self.base_path.glob("*.json"):
            key = file_path.stem
            if prefix is None or key.startswith(prefix):
                keys.append(key)
        return keys


class PickleFileStore(DataStore):
    """
    Pickle-based storage for Python objects.
    More efficient but not human-readable.
    """

    def __init__(self, base_path: str = "./data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key."""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.base_path / f"{safe_key}.pkl"

    def save(self, key: str, data: Any) -> bool:
        """Save data with pickle."""
        try:
            file_path = self._get_file_path(key)
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"Error saving {key}: {e}")
            return False

    def load(self, key: str) -> Optional[Any]:
        """Load data from pickle."""
        try:
            file_path = self._get_file_path(key)
            if not file_path.exists():
                return None

            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Error loading {key}: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a file."""
        try:
            file_path = self._get_file_path(key)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if file exists."""
        return self._get_file_path(key).exists()

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """List all pickle files."""
        keys = []
        for file_path in self.base_path.glob("*.pkl"):
            key = file_path.stem
            if prefix is None or key.startswith(prefix):
                keys.append(key)
        return keys


class DataPersistenceService:
    """
    Main service for data persistence operations.
    Facade pattern for data storage.
    """

    def __init__(self, storage_backend: str = "json", data_path: str = "./data"):
        """
        Initialize persistence service.

        Args:
            storage_backend: 'json' or 'pickle'
            data_path: Base path for data storage
        """
        if storage_backend == "json":
            self.store: DataStore = JSONFileStore(data_path)
        elif storage_backend == "pickle":
            self.store: DataStore = PickleFileStore(data_path)
        else:
            raise ValueError(f"Unknown storage backend: {storage_backend}")

    # Patient operations
    def save_patient(self, patient: Patient) -> bool:
        """Save a patient profile."""
        key = f"patient_{patient.patient_id}"
        return self.store.save(key, patient.to_dict())

    def load_patient(self, patient_id: str) -> Optional[Dict]:
        """Load a patient profile."""
        key = f"patient_{patient_id}"
        return self.store.load(key)

    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient profile."""
        key = f"patient_{patient_id}"
        return self.store.delete(key)

    def list_patients(self) -> List[str]:
        """List all patient IDs."""
        keys = self.store.list_keys(prefix="patient_")
        return [key.replace("patient_", "") for key in keys]

    # Game state operations
    def save_game_state(self, game_state: GameState) -> bool:
        """Save a game state."""
        key = f"game_{game_state.game_id}"
        return self.store.save(key, game_state.to_dict())

    def load_game_state(self, game_id: str) -> Optional[Dict]:
        """Load a game state."""
        key = f"game_{game_id}"
        return self.store.load(key)

    def list_patient_games(self, patient_id: str) -> List[str]:
        """List all game IDs for a patient."""
        # This requires loading all games and filtering
        # More efficient with a database backend
        all_game_keys = self.store.list_keys(prefix="game_")
        patient_games = []

        for key in all_game_keys:
            game_data = self.store.load(key)
            if game_data and game_data.get('patient_id') == patient_id:
                game_id = key.replace("game_", "")
                patient_games.append(game_id)

        return patient_games

    # Content operations
    def save_content_item(self, content: ContentItem) -> bool:
        """Save a content item."""
        key = f"content_{content.content_id}"
        return self.store.save(key, content.to_dict())

    def load_content_item(self, content_id: str) -> Optional[Dict]:
        """Load a content item."""
        key = f"content_{content_id}"
        return self.store.load(key)

    def list_content(self) -> List[str]:
        """List all content IDs."""
        keys = self.store.list_keys(prefix="content_")
        return [key.replace("content_", "") for key in keys]

    # Session operations
    def save_session(self, session: GameSession) -> bool:
        """Save a game session."""
        key = f"session_{session.session_id}"
        return self.store.save(key, session.get_session_summary())

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a game session."""
        key = f"session_{session_id}"
        return self.store.load(key)

    # Backup and export
    def export_patient_data(self, patient_id: str, export_path: str) -> bool:
        """
        Export all data for a patient (GDPR compliance).

        Args:
            patient_id: Patient ID
            export_path: Path to export file

        Returns:
            True if successful
        """
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'patient_id': patient_id,
                'patient_profile': self.load_patient(patient_id),
                'games': [],
                'sessions': []
            }

            # Get all games for patient
            game_ids = self.list_patient_games(patient_id)
            for game_id in game_ids:
                game_data = self.load_game_state(game_id)
                if game_data:
                    export_data['games'].append(game_data)

            # Save to file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

            return True

        except Exception as e:
            print(f"Error exporting patient data: {e}")
            return False

    def import_patient_data(self, import_path: str) -> bool:
        """
        Import patient data from export file.

        Args:
            import_path: Path to import file

        Returns:
            True if successful
        """
        try:
            with open(import_path, 'r') as f:
                import_data = json.load(f)

            patient_id = import_data['patient_id']

            # Save patient profile
            if import_data.get('patient_profile'):
                self.store.save(
                    f"patient_{patient_id}",
                    import_data['patient_profile']
                )

            # Save games
            for game_data in import_data.get('games', []):
                game_id = game_data.get('game_id')
                if game_id:
                    self.store.save(f"game_{game_id}", game_data)

            return True

        except Exception as e:
            print(f"Error importing patient data: {e}")
            return False

    def clear_old_data(self, days: int = 90) -> int:
        """
        Clear data older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of items deleted
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        # Clear old game states
        game_keys = self.store.list_keys(prefix="game_")
        for key in game_keys:
            game_data = self.store.load(key)
            if game_data and 'start_time' in game_data:
                try:
                    game_time = datetime.fromisoformat(game_data['start_time']).timestamp()
                    if game_time < cutoff_date:
                        if self.store.delete(key):
                            deleted_count += 1
                except:
                    pass

        return deleted_count
