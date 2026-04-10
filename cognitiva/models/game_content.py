"""
Game content management models.
Implements Repository pattern for content management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
from pathlib import Path
import uuid


class ContentCategory(Enum):
    """Content categories matching patient interests."""
    SPORTS = "sports"
    FAMILY = "family"
    ART = "art"
    PROFESSION = "profession"
    MUSIC = "music"
    NATURE = "nature"
    HOBBIES = "hobbies"
    TRAVEL = "travel"
    FOOD = "food"
    PETS = "pets"
    GENERIC = "generic"


class ContentType(Enum):
    """Types of media content."""
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TEXT = "text"
    THREE_D_MODEL = "3d_model"  # For future AR/VR


@dataclass
class ContentItem:
    """
    Represents a single piece of content (image, sound, text, etc.)
    Value Object pattern.
    """
    content_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ContentCategory = ContentCategory.GENERIC
    content_type: ContentType = ContentType.IMAGE
    file_path: str = ""
    thumbnail_path: Optional[str] = None
    title: str = ""
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    difficulty_rating: int = 1  # 1-5, for content complexity
    emotional_valence: str = "neutral"  # positive, neutral, negative

    # Metadata for personalization
    patient_specific: bool = False
    patient_ids: Set[str] = field(default_factory=set)

    # AR/VR metadata
    spatial_metadata: Dict = field(default_factory=dict)  # For 3D positioning

    def __post_init__(self):
        if not 1 <= self.difficulty_rating <= 5:
            raise ValueError("Difficulty rating must be between 1 and 5")

    def is_accessible_by_patient(self, patient_id: str) -> bool:
        """Check if content is available for a specific patient."""
        if not self.patient_specific:
            return True
        return patient_id in self.patient_ids

    def add_tag(self, tag: str) -> None:
        """Add a tag to the content."""
        self.tags.add(tag.lower())

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            'content_id': self.content_id,
            'category': self.category.value,
            'content_type': self.content_type.value,
            'file_path': self.file_path,
            'thumbnail_path': self.thumbnail_path,
            'title': self.title,
            'description': self.description,
            'tags': list(self.tags),
            'difficulty_rating': self.difficulty_rating,
            'emotional_valence': self.emotional_valence,
            'patient_specific': self.patient_specific,
            'patient_ids': list(self.patient_ids),
            'spatial_metadata': self.spatial_metadata
        }


class GameContent:
    """
    Repository pattern for managing game content.
    Centralizes content storage and retrieval logic.
    """

    def __init__(self):
        self._content: Dict[str, ContentItem] = {}
        self._category_index: Dict[ContentCategory, Set[str]] = {
            cat: set() for cat in ContentCategory
        }
        self._tag_index: Dict[str, Set[str]] = {}

    def add_content(self, content: ContentItem) -> None:
        """Add content item to the repository."""
        self._content[content.content_id] = content
        self._category_index[content.category].add(content.content_id)

        # Update tag index
        for tag in content.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(content.content_id)

    def get_content(self, content_id: str) -> Optional[ContentItem]:
        """Retrieve content by ID."""
        return self._content.get(content_id)

    def get_by_category(self, category: ContentCategory,
                       patient_id: Optional[str] = None) -> List[ContentItem]:
        """Get all content in a category, optionally filtered by patient access."""
        content_ids = self._category_index.get(category, set())
        contents = [self._content[cid] for cid in content_ids]

        if patient_id:
            contents = [c for c in contents if c.is_accessible_by_patient(patient_id)]

        return contents

    def get_by_tags(self, tags: List[str], match_all: bool = False) -> List[ContentItem]:
        """Get content by tags. If match_all=True, content must have all tags."""
        if not tags:
            return []

        tag_sets = [self._tag_index.get(tag.lower(), set()) for tag in tags]

        if match_all:
            # Intersection of all tag sets
            content_ids = set.intersection(*tag_sets) if tag_sets else set()
        else:
            # Union of all tag sets
            content_ids = set.union(*tag_sets) if tag_sets else set()

        return [self._content[cid] for cid in content_ids]

    def get_personalized_content(self, patient_id: str,
                                category: Optional[ContentCategory] = None,
                                limit: Optional[int] = None) -> List[ContentItem]:
        """Get content personalized for a specific patient."""
        if category:
            contents = self.get_by_category(category, patient_id)
        else:
            contents = [c for c in self._content.values()
                       if c.is_accessible_by_patient(patient_id)]

        # Prioritize patient-specific content
        patient_specific = [c for c in contents if patient_id in c.patient_ids]
        generic = [c for c in contents if not c.patient_specific]

        result = patient_specific + generic

        if limit:
            return result[:limit]
        return result

    def search_content(self, query: str) -> List[ContentItem]:
        """Search content by title or description."""
        query_lower = query.lower()
        return [
            c for c in self._content.values()
            if query_lower in c.title.lower() or query_lower in c.description.lower()
        ]

    def remove_content(self, content_id: str) -> bool:
        """Remove content from repository."""
        if content_id not in self._content:
            return False

        content = self._content[content_id]

        # Remove from category index
        self._category_index[content.category].discard(content_id)

        # Remove from tag index
        for tag in content.tags:
            self._tag_index[tag].discard(content_id)

        # Remove from main storage
        del self._content[content_id]
        return True

    def get_all_content(self) -> List[ContentItem]:
        """Get all content items."""
        return list(self._content.values())

    def get_content_count(self) -> int:
        """Get total number of content items."""
        return len(self._content)
