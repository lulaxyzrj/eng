# 🚀 Dev Hero

A typing game for developers! Test your typing speed with code snippets, programming keywords, error messages, and classic dev memes.

## 🎮 How to Play

1. Run the game:
   ```bash
   python main.py
   ```

2. Type the displayed challenge as fast and accurately as you can
3. Press Enter to submit your answer
4. See your WPM (Words Per Minute), accuracy, and stats
5. Keep playing to improve your score!

## 📁 Project Structure

```
dev_hero/
├── main.py          # Main entry point
├── game.py          # Game logic
├── codes.py         # Challenge collection (snippets, memes, keywords)
├── timer.py         # Timing utilities
├── score.py         # WPM and accuracy calculations
├── tests/
│   └── test_game.py # Unit tests
└── README.md        # This file
```

## 🎯 Features

- **Multiple Challenge Types:**
  - Python code snippets
  - JavaScript snippets
  - Error messages
  - Dev memes
  - Programming keywords

- **Statistics:**
  - WPM (Words Per Minute)
  - Accuracy percentage
  - Character-by-character comparison
  - Best WPM tracking
  - Average stats across rounds

## 🧪 Running Tests

```bash
python -m pytest tests/test_game.py
# or
python tests/test_game.py
```

## 🎨 Commands

- Type normally and press Enter to submit
- Type `quit` or `exit` to end the game
- Type `stats` to see your statistics

## 📝 Example Challenges

- `from pprint import pprint`
- `Merge conflict detected`
- `Works on my machine`
- `lambda x: x * 2`
- `I have no idea why this works`

Enjoy practicing your typing skills! 💻✨

