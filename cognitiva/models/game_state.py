"""
Game state management models.
Implements State pattern and Command pattern for game flow.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
import uuid


class GameDifficulty(Enum):
    """Difficulty levels with different configurations."""
    EASY = "easy"  # 4x3 grid, 6 pairs
    MEDIUM = "medium"  # 4x4 grid, 8 pairs
    HARD = "hard"  # 6x4 grid, 12 pairs
    EXPERT = "expert"  # 6x6 grid, 18 pairs
    CUSTOM = "custom"  # User-defined


class GamePhase(Enum):
    """Phases of the game lifecycle."""
    SETUP = "setup"
    PREVIEW = "preview"  # Optional: show all cards briefly
    PLAYING = "playing"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class DifficultyConfig:
    """Configuration for each difficulty level."""
    grid_rows: int
    grid_cols: int
    num_pairs: int
    time_limit: Optional[int] = None  # seconds, None for unlimited
    preview_time: int = 3  # seconds to show all cards at start
    allow_hints: bool = True
    hint_penalty: int = 5  # seconds added to time for using hint
    match_time_bonus: int = 2  # seconds subtracted for quick matches


# Default configurations for each difficulty
DIFFICULTY_CONFIGS = {
    GameDifficulty.EASY: DifficultyConfig(
        grid_rows=3, grid_cols=4, num_pairs=6,
        time_limit=180, preview_time=5, allow_hints=True
    ),
    GameDifficulty.MEDIUM: DifficultyConfig(
        grid_rows=4, grid_cols=4, num_pairs=8,
        time_limit=240, preview_time=3, allow_hints=True
    ),
    GameDifficulty.HARD: DifficultyConfig(
        grid_rows=4, grid_cols=6, num_pairs=12,
        time_limit=300, preview_time=2, allow_hints=False
    ),
    GameDifficulty.EXPERT: DifficultyConfig(
        grid_rows=6, grid_cols=6, num_pairs=18,
        time_limit=420, preview_time=0, allow_hints=False
    )
}


@dataclass
class GameMove:
    """
    Represents a single move in the game.
    Command pattern for move history and undo functionality.
    """
    move_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    card_ids: Tuple[str, str] = ("", "")
    was_match: bool = False
    time_taken: float = 0.0  # seconds since last move

    def to_dict(self) -> Dict:
        """Serialize move to dictionary."""
        return {
            'move_id': self.move_id,
            'timestamp': self.timestamp.isoformat(),
            'card_ids': list(self.card_ids),
            'was_match': self.was_match,
            'time_taken': self.time_taken
        }


@dataclass
class GameMetrics:
    """Tracks performance metrics for cognitive assessment."""
    total_moves: int = 0
    successful_matches: int = 0
    failed_attempts: int = 0
    hints_used: int = 0
    total_time: float = 0.0  # seconds
    average_move_time: float = 0.0
    accuracy_rate: float = 0.0
    memory_score: float = 0.0  # Calculated score based on performance

    # Advanced metrics
    first_attempt_matches: int = 0  # Matches on first try
    consecutive_matches: int = 0  # Current streak
    best_streak: int = 0
    cards_remembered: int = 0  # Cards correctly recalled after being revealed

    def update(self, move: GameMove, total_pairs: int) -> None:
        """Update metrics based on a game move."""
        self.total_moves += 1

        if move.was_match:
            self.successful_matches += 1
            self.consecutive_matches += 1
            self.best_streak = max(self.best_streak, self.consecutive_matches)
        else:
            self.failed_attempts += 1
            self.consecutive_matches = 0

        self.total_time += move.time_taken
        self.average_move_time = self.total_time / self.total_moves

        # Calculate accuracy rate
        total_attempts = self.successful_matches + self.failed_attempts
        if total_attempts > 0:
            self.accuracy_rate = self.successful_matches / total_attempts

        # Calculate memory score (0-100)
        if self.total_moves > 0:
            efficiency = total_pairs / self.total_moves  # Ideal is 1.0
            time_factor = max(0, 1 - (self.average_move_time / 10))  # Penalize slow moves
            self.memory_score = min(100, (efficiency * 0.6 +
                                         self.accuracy_rate * 0.3 +
                                         time_factor * 0.1) * 100)

    def to_dict(self) -> Dict:
        """Serialize metrics to dictionary."""
        return {
            'total_moves': self.total_moves,
            'successful_matches': self.successful_matches,
            'failed_attempts': self.failed_attempts,
            'hints_used': self.hints_used,
            'total_time': self.total_time,
            'average_move_time': self.average_move_time,
            'accuracy_rate': self.accuracy_rate,
            'memory_score': self.memory_score,
            'first_attempt_matches': self.first_attempt_matches,
            'best_streak': self.best_streak,
            'cards_remembered': self.cards_remembered
        }


@dataclass
class GameState:
    """
    Central state object for the memory game.
    State pattern implementation.
    """
    game_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""
    difficulty: GameDifficulty = GameDifficulty.MEDIUM
    config: DifficultyConfig = field(default_factory=lambda: DIFFICULTY_CONFIGS[GameDifficulty.MEDIUM])
    phase: GamePhase = GamePhase.SETUP

    # Game data
    card_ids: List[str] = field(default_factory=list)
    flipped_cards: List[str] = field(default_factory=list)  # Currently face-up cards
    matched_pairs: List[str] = field(default_factory=list)  # IDs of matched pairs

    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    elapsed_time: float = 0.0
    last_move_time: Optional[datetime] = None

    # Metrics and history
    metrics: GameMetrics = field(default_factory=GameMetrics)
    move_history: List[GameMove] = field(default_factory=list)

    # Settings
    sound_enabled: bool = True
    animations_enabled: bool = True
    auto_flip_delay: float = 1.0  # seconds before mismatched cards flip back

    def start_game(self) -> None:
        """Start the game timer and set phase to playing."""
        self.phase = GamePhase.PLAYING
        self.start_time = datetime.now()
        self.last_move_time = self.start_time

    def pause_game(self) -> None:
        """Pause the game."""
        if self.phase == GamePhase.PLAYING:
            self.phase = GamePhase.PAUSED

    def resume_game(self) -> None:
        """Resume from pause."""
        if self.phase == GamePhase.PAUSED:
            self.phase = GamePhase.PLAYING
            self.last_move_time = datetime.now()

    def complete_game(self) -> None:
        """Mark game as completed."""
        self.phase = GamePhase.COMPLETED
        self.end_time = datetime.now()
        if self.start_time:
            self.elapsed_time = (self.end_time - self.start_time).total_seconds()

    def add_move(self, card1_id: str, card2_id: str, was_match: bool) -> GameMove:
        """Record a move and update metrics."""
        current_time = datetime.now()
        time_taken = 0.0

        if self.last_move_time:
            time_taken = (current_time - self.last_move_time).total_seconds()

        move = GameMove(
            card_ids=(card1_id, card2_id),
            was_match=was_match,
            time_taken=time_taken,
            timestamp=current_time
        )

        self.move_history.append(move)
        self.metrics.update(move, self.config.num_pairs)
        self.last_move_time = current_time

        if was_match:
            # Clear flipped cards after match
            self.flipped_cards.clear()

        return move

    def is_complete(self) -> bool:
        """Check if all pairs have been matched."""
        return len(self.matched_pairs) == self.config.num_pairs

    def get_remaining_time(self) -> Optional[float]:
        """Get remaining time if time limit is set."""
        if not self.config.time_limit or not self.start_time:
            return None

        elapsed = (datetime.now() - self.start_time).total_seconds()
        remaining = self.config.time_limit - elapsed
        return max(0, remaining)

    def to_dict(self) -> Dict:
        """Serialize game state to dictionary."""
        return {
            'game_id': self.game_id,
            'patient_id': self.patient_id,
            'difficulty': self.difficulty.value,
            'phase': self.phase.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'elapsed_time': self.elapsed_time,
            'metrics': self.metrics.to_dict(),
            'move_count': len(self.move_history),
            'matched_pairs': len(self.matched_pairs),
            'total_pairs': self.config.num_pairs,
            'is_complete': self.is_complete()
        }


@dataclass
class GameSession:
    """
    Represents a complete game session with full history.
    Aggregate root pattern.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str = ""
    game_states: List[GameState] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    # Session-level metrics
    total_games_played: int = 0
    total_time: float = 0.0
    average_score: float = 0.0

    def add_game(self, game_state: GameState) -> None:
        """Add a completed game to the session."""
        self.game_states.append(game_state)
        self.total_games_played += 1
        self.total_time += game_state.elapsed_time

        # Update average score
        total_score = sum(g.metrics.memory_score for g in self.game_states)
        self.average_score = total_score / len(self.game_states)

    def get_session_summary(self) -> Dict:
        """Get a summary of the entire session."""
        return {
            'session_id': self.session_id,
            'patient_id': self.patient_id,
            'total_games': self.total_games_played,
            'total_time': self.total_time,
            'average_score': self.average_score,
            'created_at': self.created_at.isoformat(),
            'games': [g.to_dict() for g in self.game_states]
        }
