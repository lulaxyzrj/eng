"""
Score calculation utilities for WPM and accuracy.
"""


def calculate_wpm(characters_typed, time_seconds):
    """Calculate Words Per Minute (WPM).
    
    Standard: 5 characters = 1 word
    
    Args:
        characters_typed: Number of characters typed
        time_seconds: Time taken in seconds
    
    Returns:
        float: WPM score, or 0 if time is 0
    """
    if time_seconds == 0:
        return 0.0
    
    words = characters_typed / 5.0
    minutes = time_seconds / 60.0
    return words / minutes if minutes > 0 else 0.0


def calculate_accuracy(correct_chars, total_chars):
    """Calculate typing accuracy percentage.
    
    Args:
        correct_chars: Number of correctly typed characters
        total_chars: Total number of characters in the challenge
    
    Returns:
        float: Accuracy percentage (0-100)
    """
    if total_chars == 0:
        return 100.0
    
    return (correct_chars / total_chars) * 100.0


def count_correct_characters(target, user_input):
    """Count how many characters match between target and user input.
    
    Args:
        target: The target string to type
        user_input: What the user actually typed
    
    Returns:
        tuple: (correct_chars, total_chars)
            - correct_chars: Number of matching characters
            - total_chars: Length of target string
    """
    total_chars = len(target)
    correct_chars = 0
    
    for i, char in enumerate(user_input):
        if i < total_chars and char == target[i]:
            correct_chars += 1
    
    return correct_chars, total_chars


def calculate_stats(target, user_input, time_seconds):
    """Calculate all stats for a typing attempt.
    
    Args:
        target: The target string to type
        user_input: What the user actually typed
        time_seconds: Time taken in seconds
    
    Returns:
        dict: Dictionary with 'wpm', 'accuracy', 'correct_chars', 'total_chars', 'time'
    """
    correct_chars, total_chars = count_correct_characters(target, user_input)
    wpm = calculate_wpm(correct_chars, time_seconds)
    accuracy = calculate_accuracy(correct_chars, total_chars)
    
    return {
        'wpm': round(wpm, 2),
        'accuracy': round(accuracy, 2),
        'correct_chars': correct_chars,
        'total_chars': total_chars,
        'time': round(time_seconds, 2),
    }

