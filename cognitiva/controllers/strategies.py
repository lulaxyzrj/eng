"""
Strategy pattern implementation for different game difficulties and behaviors.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import random
from ..models.game_state import GameDifficulty, DifficultyConfig, DIFFICULTY_CONFIGS
from ..models.card import Card


class DifficultyStrategy(ABC):
    """
    Abstract strategy for difficulty-specific game behavior.
    Strategy pattern.
    """

    def __init__(self, config: DifficultyConfig):
        self.config = config

    @abstractmethod
    def should_shuffle_aggressive(self) -> bool:
        """Determine if cards should be shuffled more aggressively."""
        pass

    @abstractmethod
    def calculate_score_multiplier(self) -> float:
        """Get score multiplier for this difficulty."""
        pass

    @abstractmethod
    def get_hint_behavior(self) -> str:
        """Define hint behavior: 'highlight', 'brief', 'none'."""
        pass

    def generate_grid_positions(self) -> List[Tuple[int, int]]:
        """Generate all valid grid positions."""
        positions = []
        for row in range(self.config.grid_rows):
            for col in range(self.config.grid_cols):
                positions.append((row, col))
        return positions

    def shuffle_positions(self, positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Shuffle positions based on difficulty strategy."""
        shuffled = positions.copy()
        if self.should_shuffle_aggressive():
            # Multiple shuffle passes for harder difficulties
            for _ in range(3):
                random.shuffle(shuffled)
        else:
            random.shuffle(shuffled)
        return shuffled


class EasyStrategy(DifficultyStrategy):
    """Strategy for easy difficulty."""

    def __init__(self):
        super().__init__(DIFFICULTY_CONFIGS[GameDifficulty.EASY])

    def should_shuffle_aggressive(self) -> bool:
        return False

    def calculate_score_multiplier(self) -> float:
        return 1.0

    def get_hint_behavior(self) -> str:
        return 'highlight'  # Show clear visual hints


class MediumStrategy(DifficultyStrategy):
    """Strategy for medium difficulty."""

    def __init__(self):
        super().__init__(DIFFICULTY_CONFIGS[GameDifficulty.MEDIUM])

    def should_shuffle_aggressive(self) -> bool:
        return False

    def calculate_score_multiplier(self) -> float:
        return 1.5

    def get_hint_behavior(self) -> str:
        return 'brief'  # Brief hint


class HardStrategy(DifficultyStrategy):
    """Strategy for hard difficulty."""

    def __init__(self):
        super().__init__(DIFFICULTY_CONFIGS[GameDifficulty.HARD])

    def should_shuffle_aggressive(self) -> bool:
        return True

    def calculate_score_multiplier(self) -> float:
        return 2.0

    def get_hint_behavior(self) -> str:
        return 'none'  # No hints


class ExpertStrategy(DifficultyStrategy):
    """Strategy for expert difficulty."""

    def __init__(self):
        super().__init__(DIFFICULTY_CONFIGS[GameDifficulty.EXPERT])

    def should_shuffle_aggressive(self) -> bool:
        return True

    def calculate_score_multiplier(self) -> float:
        return 3.0

    def get_hint_behavior(self) -> str:
        return 'none'


class CustomStrategy(DifficultyStrategy):
    """Strategy for custom difficulty configurations."""

    def __init__(self, config: DifficultyConfig):
        super().__init__(config)
        self._shuffle_aggressive = config.grid_rows * config.grid_cols > 20
        self._hint_behavior = 'highlight' if config.allow_hints else 'none'

    def should_shuffle_aggressive(self) -> bool:
        return self._shuffle_aggressive

    def calculate_score_multiplier(self) -> float:
        # Calculate based on grid size
        total_cards = self.config.grid_rows * self.config.grid_cols
        return 1.0 + (total_cards / 20)  # Scales with complexity

    def get_hint_behavior(self) -> str:
        return self._hint_behavior


class CardSelectionStrategy(ABC):
    """
    Strategy for selecting which content to use in the game.
    Allows for different content selection algorithms.
    """

    @abstractmethod
    def select_content_ids(self, available_content_ids: List[str],
                          num_pairs: int) -> List[str]:
        """Select content IDs for the game."""
        pass


class RandomSelectionStrategy(CardSelectionStrategy):
    """Random selection of content."""

    def select_content_ids(self, available_content_ids: List[str],
                          num_pairs: int) -> List[str]:
        if len(available_content_ids) < num_pairs:
            raise ValueError(f"Not enough content: need {num_pairs}, have {len(available_content_ids)}")
        return random.sample(available_content_ids, num_pairs)


class PersonalizedSelectionStrategy(CardSelectionStrategy):
    """
    Weighted selection based on patient interests and importance.
    Prioritizes high-importance and emotionally positive content.
    """

    def __init__(self, content_weights: Optional[dict] = None):
        self.content_weights = content_weights or {}

    def select_content_ids(self, available_content_ids: List[str],
                          num_pairs: int) -> List[str]:
        if len(available_content_ids) < num_pairs:
            raise ValueError(f"Not enough content: need {num_pairs}, have {len(available_content_ids)}")

        # Use weights if available, otherwise equal probability
        if self.content_weights:
            weights = [self.content_weights.get(cid, 1.0) for cid in available_content_ids]
            return random.choices(available_content_ids, weights=weights, k=num_pairs)
        else:
            return random.sample(available_content_ids, num_pairs)


class AdaptiveSelectionStrategy(CardSelectionStrategy):
    """
    Adaptive selection based on previous performance.
    Focuses on content the patient struggled with.
    """

    def __init__(self, performance_history: Optional[dict] = None):
        self.performance_history = performance_history or {}

    def select_content_ids(self, available_content_ids: List[str],
                          num_pairs: int) -> List[str]:
        if len(available_content_ids) < num_pairs:
            raise ValueError(f"Not enough content: need {num_pairs}, have {len(available_content_ids)}")

        # Select mix of struggled content (60%) and new/successful content (40%)
        struggled = []
        other = []

        for cid in available_content_ids:
            accuracy = self.performance_history.get(cid, {}).get('accuracy', 1.0)
            if accuracy < 0.7:  # Struggled with this content
                struggled.append(cid)
            else:
                other.append(cid)

        # Calculate how many from each group
        num_struggled = min(len(struggled), int(num_pairs * 0.6))
        num_other = num_pairs - num_struggled

        selected = []
        if struggled:
            selected.extend(random.sample(struggled, min(num_struggled, len(struggled))))
        if other:
            selected.extend(random.sample(other, min(num_other, len(other))))

        # Fill remaining with random if needed
        if len(selected) < num_pairs:
            remaining = [cid for cid in available_content_ids if cid not in selected]
            selected.extend(random.sample(remaining, num_pairs - len(selected)))

        return selected


def get_difficulty_strategy(difficulty: GameDifficulty,
                           custom_config: Optional[DifficultyConfig] = None) -> DifficultyStrategy:
    """
    Factory method to get the appropriate difficulty strategy.
    Factory pattern.
    """
    strategies = {
        GameDifficulty.EASY: EasyStrategy,
        GameDifficulty.MEDIUM: MediumStrategy,
        GameDifficulty.HARD: HardStrategy,
        GameDifficulty.EXPERT: ExpertStrategy,
    }

    if difficulty == GameDifficulty.CUSTOM:
        if custom_config is None:
            raise ValueError("Custom difficulty requires a config")
        return CustomStrategy(custom_config)

    strategy_class = strategies.get(difficulty)
    if strategy_class is None:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    return strategy_class()
