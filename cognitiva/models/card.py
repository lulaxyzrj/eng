"""
Card models for the memory game.
Implements Entity and Value Object patterns.
"""

from dataclasses import dataclass, field
from typing import Optional, Tuple
from enum import Enum
import uuid


class CardState(Enum):
    """Possible states of a memory card."""
    FACE_DOWN = "face_down"
    FACE_UP = "face_up"
    MATCHED = "matched"
    REMOVED = "removed"


@dataclass
class CardAnimation:
    """Animation configuration for cards (for AR/VR support)."""
    flip_duration: float = 0.5  # seconds
    match_animation: str = "pulse"  # pulse, glow, expand, etc.
    mismatch_animation: str = "shake"
    remove_animation: str = "fade"
    spatial_position: Optional[Tuple[float, float, float]] = None  # x, y, z for AR/VR


@dataclass
class Card:
    """
    Represents a single memory card in the game.
    Entity pattern with unique identity.
    """
    card_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content_id: str = ""  # References ContentItem
    state: CardState = CardState.FACE_DOWN
    position: Tuple[int, int] = (0, 0)  # Grid position (row, col)
    pair_id: str = ""  # ID of the matching pair

    # Visual and interaction properties
    animation_config: CardAnimation = field(default_factory=CardAnimation)
    is_interactive: bool = True
    hint_available: bool = False

    def flip(self) -> None:
        """Flip the card face up."""
        if self.state == CardState.FACE_DOWN and self.is_interactive:
            self.state = CardState.FACE_UP

    def flip_down(self) -> None:
        """Flip the card face down."""
        if self.state == CardState.FACE_UP:
            self.state = CardState.FACE_DOWN

    def mark_matched(self) -> None:
        """Mark the card as successfully matched."""
        self.state = CardState.MATCHED
        self.is_interactive = False

    def remove(self) -> None:
        """Remove the card from play."""
        self.state = CardState.REMOVED
        self.is_interactive = False

    def reset(self) -> None:
        """Reset card to initial state."""
        self.state = CardState.FACE_DOWN
        self.is_interactive = True

    def is_face_up(self) -> bool:
        """Check if card is currently face up."""
        return self.state == CardState.FACE_UP

    def is_matched(self) -> bool:
        """Check if card has been matched."""
        return self.state == CardState.MATCHED

    def to_dict(self) -> dict:
        """Serialize card to dictionary."""
        return {
            'card_id': self.card_id,
            'content_id': self.content_id,
            'state': self.state.value,
            'position': self.position,
            'pair_id': self.pair_id,
            'is_interactive': self.is_interactive,
            'hint_available': self.hint_available
        }


@dataclass
class CardPair:
    """
    Represents a matching pair of cards.
    Value Object pattern.
    """
    pair_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    card1_id: str = ""
    card2_id: str = ""
    content_id: str = ""  # The shared content between the pair
    is_matched: bool = False

    def contains_card(self, card_id: str) -> bool:
        """Check if a card belongs to this pair."""
        return card_id in (self.card1_id, self.card2_id)

    def get_partner_id(self, card_id: str) -> Optional[str]:
        """Get the ID of the partner card."""
        if card_id == self.card1_id:
            return self.card2_id
        elif card_id == self.card2_id:
            return self.card1_id
        return None

    def mark_matched(self) -> None:
        """Mark this pair as successfully matched."""
        self.is_matched = True
