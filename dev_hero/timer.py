"""
Timer utilities for measuring typing speed and accuracy.
"""

import time


class Timer:
    """Simple timer for measuring elapsed time."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """Start the timer."""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self):
        """Stop the timer."""
        if self.start_time is not None:
            self.end_time = time.time()
    
    def elapsed(self):
        """Get elapsed time in seconds.
        
        Returns:
            float: Elapsed time in seconds, or None if timer hasn't started
        """
        if self.start_time is None:
            return None
        
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
    
    def reset(self):
        """Reset the timer."""
        self.start_time = None
        self.end_time = None

