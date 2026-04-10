"""
Main game logic for Dev Hero typing game.
"""

from codes import get_random_challenge
from timer import Timer
from score import calculate_stats


class DevHeroGame:
    """Main game class for Dev Hero typing game."""
    
    def __init__(self):
        self.timer = Timer()
        self.rounds_played = 0
        self.total_wpm = 0.0
        self.total_accuracy = 0.0
        self.best_wpm = 0.0
    
    def get_challenge(self):
        """Get a random challenge to type.
        
        Returns:
            str: Random challenge string
        """
        return get_random_challenge()
    
    def start_round(self):
        """Start a new typing round.
        
        Returns:
            str: The challenge to type
        """
        challenge = self.get_challenge()
        self.timer.start()
        return challenge
    
    def finish_round(self, target, user_input):
        """Finish a typing round and calculate stats.
        
        Args:
            target: The target string that should have been typed
            user_input: What the user actually typed
        
        Returns:
            dict: Statistics for this round
        """
        self.timer.stop()
        time_elapsed = self.timer.elapsed()
        
        stats = calculate_stats(target, user_input, time_elapsed)
        
        # Update game statistics
        self.rounds_played += 1
        self.total_wpm += stats['wpm']
        self.total_accuracy += stats['accuracy']
        
        if stats['wpm'] > self.best_wpm:
            self.best_wpm = stats['wpm']
        
        self.timer.reset()
        
        return stats
    
    def is_perfect_match(self, target, user_input):
        """Check if user input perfectly matches target.
        
        Args:
            target: The target string
            user_input: The user's input
        
        Returns:
            bool: True if perfect match, False otherwise
        """
        return target == user_input
    
    def get_average_stats(self):
        """Get average statistics across all rounds.
        
        Returns:
            dict: Average WPM and accuracy
        """
        if self.rounds_played == 0:
            return {'avg_wpm': 0.0, 'avg_accuracy': 0.0}
        
        return {
            'avg_wpm': round(self.total_wpm / self.rounds_played, 2),
            'avg_accuracy': round(self.total_accuracy / self.rounds_played, 2),
            'rounds': self.rounds_played,
            'best_wpm': round(self.best_wpm, 2),
        }

