"""
Patient model for personalized cognitive training.
Implements the Entity pattern for patient data management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
import uuid


class InterestCategory(Enum):
    """Categories of patient interests for content personalization."""
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


@dataclass
class PatientInterest:
    """Represents a specific interest with metadata."""
    category: InterestCategory
    name: str
    importance: int = 5  # 1-10 scale
    notes: str = ""
    media_paths: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not 1 <= self.importance <= 10:
            raise ValueError("Importance must be between 1 and 10")


@dataclass
class CognitiveProfile:
    """Tracks cognitive abilities and progress."""
    memory_score: float = 0.0
    attention_span: float = 0.0
    reaction_time: float = 0.0
    accuracy_rate: float = 0.0
    preferred_difficulty: str = "medium"
    session_duration_preference: int = 15  # minutes
    last_assessment_date: Optional[datetime] = None

    def update_scores(self, session_data: Dict[str, float]):
        """Update cognitive scores based on session performance."""
        self.memory_score = session_data.get('memory_score', self.memory_score)
        self.attention_span = session_data.get('attention_span', self.attention_span)
        self.reaction_time = session_data.get('reaction_time', self.reaction_time)
        self.accuracy_rate = session_data.get('accuracy_rate', self.accuracy_rate)
        self.last_assessment_date = datetime.now()


@dataclass
class AccessibilitySettings:
    """Accessibility and UI preferences."""
    font_size: str = "medium"  # small, medium, large, xlarge
    high_contrast: bool = False
    audio_cues: bool = True
    haptic_feedback: bool = True
    color_blind_mode: Optional[str] = None  # protanopia, deuteranopia, tritanopia
    motion_sensitivity: str = "normal"  # low, normal, high
    text_to_speech: bool = False

    def to_dict(self) -> Dict:
        """Convert settings to dictionary."""
        return {
            'font_size': self.font_size,
            'high_contrast': self.high_contrast,
            'audio_cues': self.audio_cues,
            'haptic_feedback': self.haptic_feedback,
            'color_blind_mode': self.color_blind_mode,
            'motion_sensitivity': self.motion_sensitivity,
            'text_to_speech': self.text_to_speech
        }


@dataclass
class Patient:
    """
    Patient entity with comprehensive profile for personalized cognitive training.
    Implements data validation and encapsulation.
    """
    patient_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    age: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Personalization data
    interests: List[PatientInterest] = field(default_factory=list)
    cognitive_profile: CognitiveProfile = field(default_factory=CognitiveProfile)
    accessibility: AccessibilitySettings = field(default_factory=AccessibilitySettings)

    # Medical and care team notes
    notes: str = ""
    care_team_notes: str = ""

    def __post_init__(self):
        if self.age is not None and (self.age < 0 or self.age > 150):
            raise ValueError("Invalid age value")

    def add_interest(self, interest: PatientInterest) -> None:
        """Add a new interest to the patient profile."""
        self.interests.append(interest)
        self.updated_at = datetime.now()

    def get_interests_by_category(self, category: InterestCategory) -> List[PatientInterest]:
        """Retrieve all interests in a specific category."""
        return [i for i in self.interests if i.category == category]

    def get_top_interests(self, limit: int = 5) -> List[PatientInterest]:
        """Get the most important interests."""
        return sorted(self.interests, key=lambda x: x.importance, reverse=True)[:limit]

    def update_cognitive_profile(self, session_data: Dict[str, float]) -> None:
        """Update cognitive profile based on game session."""
        self.cognitive_profile.update_scores(session_data)
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        """Serialize patient data to dictionary."""
        return {
            'patient_id': self.patient_id,
            'name': self.name,
            'age': self.age,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'interests': [
                {
                    'category': i.category.value,
                    'name': i.name,
                    'importance': i.importance,
                    'notes': i.notes,
                    'media_paths': i.media_paths
                }
                for i in self.interests
            ],
            'cognitive_profile': {
                'memory_score': self.cognitive_profile.memory_score,
                'attention_span': self.cognitive_profile.attention_span,
                'reaction_time': self.cognitive_profile.reaction_time,
                'accuracy_rate': self.cognitive_profile.accuracy_rate,
                'preferred_difficulty': self.cognitive_profile.preferred_difficulty,
                'session_duration_preference': self.cognitive_profile.session_duration_preference,
                'last_assessment_date': self.cognitive_profile.last_assessment_date.isoformat()
                    if self.cognitive_profile.last_assessment_date else None
            },
            'accessibility': self.accessibility.to_dict(),
            'notes': self.notes,
            'care_team_notes': self.care_team_notes
        }


class PatientProfile:
    """
    Facade pattern for managing patient profiles.
    Provides simplified interface for patient data operations.
    """

    def __init__(self):
        self._patients: Dict[str, Patient] = {}

    def create_patient(self, name: str, age: Optional[int] = None) -> Patient:
        """Create a new patient profile."""
        patient = Patient(name=name, age=age)
        self._patients[patient.patient_id] = patient
        return patient

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Retrieve a patient by ID."""
        return self._patients.get(patient_id)

    def update_patient(self, patient: Patient) -> None:
        """Update an existing patient."""
        patient.updated_at = datetime.now()
        self._patients[patient.patient_id] = patient

    def delete_patient(self, patient_id: str) -> bool:
        """Delete a patient profile."""
        if patient_id in self._patients:
            del self._patients[patient_id]
            return True
        return False

    def list_patients(self) -> List[Patient]:
        """Get all patients."""
        return list(self._patients.values())

    def search_patients(self, query: str) -> List[Patient]:
        """Search patients by name."""
        query_lower = query.lower()
        return [p for p in self._patients.values() if query_lower in p.name.lower()]
