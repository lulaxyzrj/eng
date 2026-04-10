"""
Main game controller implementing MVC pattern and Observer pattern.
Coordinates game logic, state management, and event handling.
"""

from typing import List, Optional, Dict, Callable
import random
from datetime import datetime

from ..models.patient import Patient
from ..models.game_content import GameContent, ContentItem
from ..models.card import Card, CardPair, CardState
from ..models.game_state import (
    GameState, GameDifficulty, GamePhase,
    DifficultyConfig, DIFFICULTY_CONFIGS
)
from .strategies import (
    get_difficulty_strategy,
    DifficultyStrategy,
    CardSelectionStrategy,
    RandomSelectionStrategy,
    PersonalizedSelectionStrategy
)


class GameEvent:
    """Event object for observer pattern."""

    def __init__(self, event_type: str, data: Dict = None):
        self.event_type = event_type
        self.data = data or {}
        self.timestamp = datetime.now()


class GameController:
    """
    Main controller for the memory game.
    Implements MVC Controller and Observer patterns.
    """

    def __init__(self, content_repository: GameContent):
        self.content_repository = content_repository
        self.game_state: Optional[GameState] = None
        self.cards: Dict[str, Card] = {}
        self.pairs: Dict[str, CardPair] = {}

        # Strategy instances
        self.difficulty_strategy: Optional[DifficultyStrategy] = None
        self.selection_strategy: CardSelectionStrategy = RandomSelectionStrategy()

        # Observer pattern: event listeners
        self._listeners: Dict[str, List[Callable]] = {}

        # Game configuration
        self.current_patient: Optional[Patient] = None

    # ===== Event System (Observer Pattern) =====

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to game events."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from game events."""
        if event_type in self._listeners:
            self._listeners[event_type].remove(callback)

    def _notify(self, event_type: str, data: Dict = None) -> None:
        """Notify all subscribers of an event."""
        event = GameEvent(event_type, data)
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                callback(event)

    # ===== Game Initialization =====

    def setup_game(self, patient: Patient, difficulty: GameDifficulty,
                  custom_config: Optional[DifficultyConfig] = None,
                  use_personalized_content: bool = True) -> GameState:
        """
        Initialize a new game session.

        Args:
            patient: Patient profile for personalization
            difficulty: Game difficulty level
            custom_config: Optional custom difficulty configuration
            use_personalized_content: Whether to use patient-specific content

        Returns:
            Initialized GameState object
        """
        self.current_patient = patient

        # Set up difficulty strategy
        self.difficulty_strategy = get_difficulty_strategy(difficulty, custom_config)
        config = custom_config if difficulty == GameDifficulty.CUSTOM else self.difficulty_strategy.config

        # Create game state
        self.game_state = GameState(
            patient_id=patient.patient_id,
            difficulty=difficulty,
            config=config,
            phase=GamePhase.SETUP
        )

        # Set up content selection strategy
        if use_personalized_content:
            weights = self._calculate_content_weights(patient)
            self.selection_strategy = PersonalizedSelectionStrategy(weights)
        else:
            self.selection_strategy = RandomSelectionStrategy()

        # Generate cards
        self._generate_cards()

        # Notify listeners
        self._notify('game_setup', {
            'game_id': self.game_state.game_id,
            'difficulty': difficulty.value,
            'patient_id': patient.patient_id
        })

        return self.game_state

    def _calculate_content_weights(self, patient: Patient) -> Dict[str, float]:
        """Calculate weights for content based on patient interests."""
        weights = {}

        # Get all available content
        all_content = self.content_repository.get_personalized_content(
            patient.patient_id
        )

        for content in all_content:
            # Base weight
            weight = 1.0

            # Boost based on patient interests
            for interest in patient.interests:
                if interest.category.value == content.category.value:
                    # Scale by importance (1-10)
                    weight += interest.importance / 10.0

            # Boost patient-specific content
            if patient.patient_id in content.patient_ids:
                weight *= 2.0

            # Adjust for emotional valence (prefer positive)
            if content.emotional_valence == 'positive':
                weight *= 1.5
            elif content.emotional_valence == 'negative':
                weight *= 0.7

            weights[content.content_id] = weight

        return weights

    def _generate_cards(self) -> None:
        """Generate cards for the game based on selected content."""
        if not self.game_state:
            raise RuntimeError("Game state not initialized")

        # Get available content for the patient
        available_content = self.content_repository.get_personalized_content(
            self.current_patient.patient_id
        )

        if len(available_content) < self.game_state.config.num_pairs:
            raise ValueError(
                f"Not enough content for game: need {self.game_state.config.num_pairs}, "
                f"have {len(available_content)}"
            )

        # Select content using strategy
        content_ids = [c.content_id for c in available_content]
        selected_ids = self.selection_strategy.select_content_ids(
            content_ids,
            self.game_state.config.num_pairs
        )

        # Generate grid positions
        positions = self.difficulty_strategy.generate_grid_positions()
        shuffled_positions = self.difficulty_strategy.shuffle_positions(positions)

        # Create card pairs
        self.cards.clear()
        self.pairs.clear()
        position_idx = 0

        for content_id in selected_ids:
            # Create a pair
            pair = CardPair(content_id=content_id)
            self.pairs[pair.pair_id] = pair

            # Create two cards for the pair
            card1 = Card(
                content_id=content_id,
                position=shuffled_positions[position_idx],
                pair_id=pair.pair_id
            )
            position_idx += 1

            card2 = Card(
                content_id=content_id,
                position=shuffled_positions[position_idx],
                pair_id=pair.pair_id
            )
            position_idx += 1

            # Link cards in pair
            pair.card1_id = card1.card_id
            pair.card2_id = card2.card_id

            # Store cards
            self.cards[card1.card_id] = card1
            self.cards[card2.card_id] = card2
            self.game_state.card_ids.extend([card1.card_id, card2.card_id])

    # ===== Game Flow Control =====

    def start_game(self) -> None:
        """Start the game."""
        if not self.game_state:
            raise RuntimeError("Game not set up")

        self.game_state.start_game()
        self._notify('game_started', {'game_id': self.game_state.game_id})

    def pause_game(self) -> None:
        """Pause the game."""
        if self.game_state:
            self.game_state.pause_game()
            self._notify('game_paused', {'game_id': self.game_state.game_id})

    def resume_game(self) -> None:
        """Resume the game."""
        if self.game_state:
            self.game_state.resume_game()
            self._notify('game_resumed', {'game_id': self.game_state.game_id})

    def end_game(self) -> Dict:
        """End the game and return final results."""
        if not self.game_state:
            raise RuntimeError("No active game")

        self.game_state.complete_game()

        # Update patient cognitive profile
        if self.current_patient:
            self.current_patient.update_cognitive_profile({
                'memory_score': self.game_state.metrics.memory_score,
                'accuracy_rate': self.game_state.metrics.accuracy_rate,
                'reaction_time': self.game_state.metrics.average_move_time,
                'attention_span': self._calculate_attention_span()
            })

        results = self.game_state.to_dict()
        self._notify('game_ended', results)

        return results

    def _calculate_attention_span(self) -> float:
        """Calculate attention span metric from game data."""
        if not self.game_state or not self.game_state.move_history:
            return 0.0

        # Analyze consistency of move times
        move_times = [m.time_taken for m in self.game_state.move_history]
        if not move_times:
            return 0.0

        # Lower variance in move times indicates better attention
        avg_time = sum(move_times) / len(move_times)
        variance = sum((t - avg_time) ** 2 for t in move_times) / len(move_times)

        # Normalize to 0-100 scale (lower variance = higher score)
        attention_score = max(0, 100 - (variance * 10))
        return attention_score

    # ===== Game Actions =====

    def flip_card(self, card_id: str) -> Dict:
        """
        Flip a card face up.

        Returns:
            Dictionary with action result and any match information
        """
        if not self.game_state or self.game_state.phase != GamePhase.PLAYING:
            return {'success': False, 'reason': 'Game not in playing state'}

        if card_id not in self.cards:
            return {'success': False, 'reason': 'Invalid card ID'}

        card = self.cards[card_id]

        # Check if card can be flipped
        if not card.is_interactive or card.is_matched():
            return {'success': False, 'reason': 'Card cannot be flipped'}

        # Check if already two cards flipped
        if len(self.game_state.flipped_cards) >= 2:
            return {'success': False, 'reason': 'Two cards already flipped'}

        # Flip the card
        card.flip()
        self.game_state.flipped_cards.append(card_id)

        self._notify('card_flipped', {
            'card_id': card_id,
            'content_id': card.content_id,
            'position': card.position
        })

        result = {'success': True, 'card': card.to_dict()}

        # Check for match if two cards are flipped
        if len(self.game_state.flipped_cards) == 2:
            match_result = self._check_match()
            result.update(match_result)

        return result

    def _check_match(self) -> Dict:
        """Check if the two flipped cards match."""
        if len(self.game_state.flipped_cards) != 2:
            return {'is_match': False}

        card1_id, card2_id = self.game_state.flipped_cards
        card1 = self.cards[card1_id]
        card2 = self.cards[card2_id]

        is_match = card1.pair_id == card2.pair_id

        # Record the move
        move = self.game_state.add_move(card1_id, card2_id, is_match)

        if is_match:
            # Mark cards as matched
            card1.mark_matched()
            card2.mark_matched()

            # Update pair status
            pair = self.pairs[card1.pair_id]
            pair.mark_matched()
            self.game_state.matched_pairs.append(pair.pair_id)

            self._notify('match_found', {
                'card_ids': [card1_id, card2_id],
                'content_id': card1.content_id,
                'move': move.to_dict()
            })

            # Check if game is complete
            if self.game_state.is_complete():
                self.end_game()

        else:
            self._notify('match_failed', {
                'card_ids': [card1_id, card2_id],
                'move': move.to_dict()
            })

            # Cards will need to be flipped back by the view

        return {
            'is_match': is_match,
            'move': move.to_dict(),
            'game_complete': self.game_state.is_complete()
        }

    def flip_cards_down(self) -> None:
        """Flip currently revealed cards back down (after failed match)."""
        if not self.game_state:
            return

        for card_id in self.game_state.flipped_cards:
            if card_id in self.cards:
                self.cards[card_id].flip_down()

        self.game_state.flipped_cards.clear()
        self._notify('cards_flipped_down', {})

    def use_hint(self) -> Optional[Dict]:
        """
        Provide a hint to the player.

        Returns:
            Hint information or None if hints not allowed
        """
        if not self.game_state or not self.game_state.config.allow_hints:
            return None

        if not self.difficulty_strategy:
            return None

        hint_behavior = self.difficulty_strategy.get_hint_behavior()
        if hint_behavior == 'none':
            return None

        # Find an unmatched pair
        unmatched_pairs = [
            pair for pair in self.pairs.values()
            if not pair.is_matched
        ]

        if not unmatched_pairs:
            return None

        # Select a random unmatched pair
        hint_pair = random.choice(unmatched_pairs)
        self.game_state.metrics.hints_used += 1

        self._notify('hint_used', {
            'pair_id': hint_pair.pair_id,
            'card_ids': [hint_pair.card1_id, hint_pair.card2_id],
            'behavior': hint_behavior
        })

        return {
            'pair_id': hint_pair.pair_id,
            'card_ids': [hint_pair.card1_id, hint_pair.card2_id],
            'behavior': hint_behavior
        }

    # ===== Query Methods =====

    def get_card(self, card_id: str) -> Optional[Card]:
        """Get a card by ID."""
        return self.cards.get(card_id)

    def get_all_cards(self) -> List[Card]:
        """Get all cards in the game."""
        return list(self.cards.values())

    def get_game_state(self) -> Optional[GameState]:
        """Get current game state."""
        return self.game_state

    def get_progress(self) -> Dict:
        """Get current game progress."""
        if not self.game_state:
            return {}

        return {
            'matched_pairs': len(self.game_state.matched_pairs),
            'total_pairs': self.game_state.config.num_pairs,
            'percentage': (len(self.game_state.matched_pairs) /
                          self.game_state.config.num_pairs * 100),
            'moves': self.game_state.metrics.total_moves,
            'time_elapsed': self.game_state.elapsed_time,
            'remaining_time': self.game_state.get_remaining_time(),
            'current_score': self.game_state.metrics.memory_score
        }

    def get_card_grid(self) -> List[List[Optional[str]]]:
        """
        Get card IDs arranged in grid format.

        Returns:
            2D list of card IDs
        """
        if not self.game_state:
            return []

        rows = self.game_state.config.grid_rows
        cols = self.game_state.config.grid_cols

        grid = [[None for _ in range(cols)] for _ in range(rows)]

        for card in self.cards.values():
            row, col = card.position
            grid[row][col] = card.card_id

        return grid
