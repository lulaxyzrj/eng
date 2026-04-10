"""
Tests for Dev Hero game logic.
"""

import unittest
import sys
import os

# Add parent directory to path to import game modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game import DevHeroGame
from score import calculate_wpm, calculate_accuracy, count_correct_characters
from timer import Timer
from codes import get_random_challenge, ALL_CHALLENGES


class TestTimer(unittest.TestCase):
    """Test Timer class."""
    
    def test_timer_start_stop(self):
        """Test timer start and stop functionality."""
        timer = Timer()
        self.assertIsNone(timer.elapsed())
        
        timer.start()
        self.assertIsNotNone(timer.elapsed())
        
        timer.stop()
        elapsed = timer.elapsed()
        self.assertIsNotNone(elapsed)
        self.assertGreater(elapsed, 0)
    
    def test_timer_reset(self):
        """Test timer reset functionality."""
        timer = Timer()
        timer.start()
        timer.stop()
        timer.reset()
        self.assertIsNone(timer.elapsed())


class TestScore(unittest.TestCase):
    """Test score calculation functions."""
    
    def test_calculate_wpm(self):
        """Test WPM calculation."""
        # 60 characters = 12 words, 1 minute = 12 WPM
        wpm = calculate_wpm(60, 60)
        self.assertEqual(wpm, 12.0)
        
        # 60 characters in 30 seconds = 24 WPM
        wpm = calculate_wpm(60, 30)
        self.assertEqual(wpm, 24.0)
        
        # Zero time should return 0
        wpm = calculate_wpm(60, 0)
        self.assertEqual(wpm, 0.0)
    
    def test_calculate_accuracy(self):
        """Test accuracy calculation."""
        # Perfect match
        accuracy = calculate_accuracy(10, 10)
        self.assertEqual(accuracy, 100.0)
        
        # Half correct
        accuracy = calculate_accuracy(5, 10)
        self.assertEqual(accuracy, 50.0)
        
        # Zero total should return 100
        accuracy = calculate_accuracy(0, 0)
        self.assertEqual(accuracy, 100.0)
    
    def test_count_correct_characters(self):
        """Test character counting."""
        correct, total = count_correct_characters("hello", "hello")
        self.assertEqual(correct, 5)
        self.assertEqual(total, 5)
        
        correct, total = count_correct_characters("hello", "hel")
        self.assertEqual(correct, 3)
        self.assertEqual(total, 5)
        
        correct, total = count_correct_characters("hello", "helxx")
        self.assertEqual(correct, 3)
        self.assertEqual(total, 5)


class TestGame(unittest.TestCase):
    """Test DevHeroGame class."""
    
    def test_get_challenge(self):
        """Test getting a challenge."""
        game = DevHeroGame()
        challenge = game.get_challenge()
        self.assertIsInstance(challenge, str)
        self.assertIn(challenge, ALL_CHALLENGES)
    
    def test_is_perfect_match(self):
        """Test perfect match detection."""
        game = DevHeroGame()
        self.assertTrue(game.is_perfect_match("hello", "hello"))
        self.assertFalse(game.is_perfect_match("hello", "helo"))
        self.assertFalse(game.is_perfect_match("hello", "hello world"))
    
    def test_finish_round(self):
        """Test finishing a round."""
        game = DevHeroGame()
        challenge = game.start_round()
        
        # Simulate some time passing
        import time
        time.sleep(0.1)
        
        stats = game.finish_round(challenge, challenge)
        self.assertIn('wpm', stats)
        self.assertIn('accuracy', stats)
        self.assertEqual(stats['accuracy'], 100.0)
        self.assertEqual(game.rounds_played, 1)
    
    def test_average_stats(self):
        """Test average statistics calculation."""
        game = DevHeroGame()
        
        # No rounds played
        stats = game.get_average_stats()
        self.assertEqual(stats['avg_wpm'], 0.0)
        self.assertEqual(stats['rounds'], 0)
        
        # Play a round
        challenge = game.start_round()
        import time
        time.sleep(0.1)
        game.finish_round(challenge, challenge)
        
        stats = game.get_average_stats()
        self.assertGreater(stats['avg_wpm'], 0)
        self.assertEqual(stats['rounds'], 1)


class TestCodes(unittest.TestCase):
    """Test codes module."""
    
    def test_get_random_challenge(self):
        """Test getting random challenge."""
        challenge = get_random_challenge()
        self.assertIsInstance(challenge, str)
        self.assertIn(challenge, ALL_CHALLENGES)
    
    def test_all_challenges_not_empty(self):
        """Test that all challenges list is not empty."""
        self.assertGreater(len(ALL_CHALLENGES), 0)


if __name__ == '__main__':
    unittest.main()

