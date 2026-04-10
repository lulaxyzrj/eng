"""
UI Manager for handling user interface and themes.
Manages theming, layout, and UI components.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from pathlib import Path
import json


@dataclass
class ThemeConfig:
    """Theme configuration for visual customization."""
    name: str = "default"

    # Color scheme
    primary_color: Tuple[int, int, int] = (100, 120, 180)
    secondary_color: Tuple[int, int, int] = (150, 170, 200)
    accent_color: Tuple[int, int, int] = (255, 200, 100)
    background_color: Tuple[int, int, int] = (245, 245, 250)
    text_color: Tuple[int, int, int] = (50, 50, 50)

    # Card styling
    card_back_image: Optional[str] = None
    card_frame_style: str = "rounded"  # rounded, square, ornate
    card_shadow: bool = True

    # Animations
    animation_style: str = "smooth"  # smooth, snappy, playful
    particle_effects: bool = True

    # Audio theme
    flip_sound: Optional[str] = None
    match_sound: Optional[str] = None
    win_sound: Optional[str] = None
    background_music: Optional[str] = None

    # Fonts
    title_font: str = "Arial"
    body_font: str = "Arial"

    def to_dict(self) -> Dict:
        """Serialize theme to dictionary."""
        return {
            'name': self.name,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'card_back_image': self.card_back_image,
            'card_frame_style': self.card_frame_style,
            'card_shadow': self.card_shadow,
            'animation_style': self.animation_style,
            'particle_effects': self.particle_effects,
            'flip_sound': self.flip_sound,
            'match_sound': self.match_sound,
            'win_sound': self.win_sound,
            'background_music': self.background_music,
            'title_font': self.title_font,
            'body_font': self.body_font
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ThemeConfig':
        """Create theme from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    @classmethod
    def load_from_file(cls, path: str) -> 'ThemeConfig':
        """Load theme from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_to_file(self, path: str) -> None:
        """Save theme to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class ThemeManager:
    """
    Manages multiple themes and theme switching.
    Singleton pattern.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.themes: Dict[str, ThemeConfig] = {}
        self.current_theme: Optional[ThemeConfig] = None
        self._load_default_themes()
        self._initialized = True

    def _load_default_themes(self) -> None:
        """Load default themes."""
        # Default theme
        default_theme = ThemeConfig(name="default")
        self.themes["default"] = default_theme

        # Ocean theme
        ocean_theme = ThemeConfig(
            name="ocean",
            primary_color=(52, 152, 219),
            secondary_color=(155, 200, 230),
            accent_color=(241, 196, 15),
            background_color=(236, 240, 241),
            text_color=(44, 62, 80)
        )
        self.themes["ocean"] = ocean_theme

        # Forest theme
        forest_theme = ThemeConfig(
            name="forest",
            primary_color=(39, 174, 96),
            secondary_color=(149, 200, 150),
            accent_color=(230, 126, 34),
            background_color=(236, 240, 241),
            text_color=(44, 62, 80)
        )
        self.themes["forest"] = forest_theme

        # Sunset theme
        sunset_theme = ThemeConfig(
            name="sunset",
            primary_color=(231, 76, 60),
            secondary_color=(242, 120, 100),
            accent_color=(241, 196, 15),
            background_color=(250, 240, 230),
            text_color=(52, 73, 94)
        )
        self.themes["sunset"] = sunset_theme

        # High contrast theme (for accessibility)
        high_contrast_theme = ThemeConfig(
            name="high_contrast",
            primary_color=(255, 255, 255),
            secondary_color=(200, 200, 200),
            accent_color=(255, 255, 0),
            background_color=(0, 0, 0),
            text_color=(255, 255, 255),
            card_shadow=False
        )
        self.themes["high_contrast"] = high_contrast_theme

        self.current_theme = default_theme

    def add_theme(self, theme: ThemeConfig) -> None:
        """Add a custom theme."""
        self.themes[theme.name] = theme

    def set_theme(self, theme_name: str) -> bool:
        """Switch to a different theme."""
        if theme_name in self.themes:
            self.current_theme = self.themes[theme_name]
            return True
        return False

    def get_theme(self, theme_name: str) -> Optional[ThemeConfig]:
        """Get a theme by name."""
        return self.themes.get(theme_name)

    def list_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.themes.keys())


@dataclass
class UIElement:
    """Base class for UI elements."""
    element_id: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    visible: bool = True
    interactive: bool = True

    def contains_point(self, point: Tuple[int, int]) -> bool:
        """Check if a point is within this element."""
        x, y = point
        elem_x, elem_y = self.position
        width, height = self.size

        return (elem_x <= x <= elem_x + width and
                elem_y <= y <= elem_y + height)


@dataclass
class Button(UIElement):
    """Button UI element."""
    text: str = ""
    on_click: Optional[Callable] = None
    background_color: Tuple[int, int, int] = (100, 120, 180)
    text_color: Tuple[int, int, int] = (255, 255, 255)
    hover_color: Tuple[int, int, int] = (120, 140, 200)
    is_hovered: bool = False

    def handle_click(self) -> None:
        """Handle button click."""
        if self.interactive and self.on_click:
            self.on_click()


@dataclass
class ProgressBar(UIElement):
    """Progress bar UI element."""
    current_value: float = 0.0
    max_value: float = 100.0
    fill_color: Tuple[int, int, int] = (100, 200, 100)
    background_color: Tuple[int, int, int] = (200, 200, 200)
    show_text: bool = True

    def get_percentage(self) -> float:
        """Get progress percentage."""
        if self.max_value == 0:
            return 0.0
        return (self.current_value / self.max_value) * 100


@dataclass
class Label(UIElement):
    """Text label UI element."""
    text: str = ""
    font_size: int = 24
    text_color: Tuple[int, int, int] = (50, 50, 50)
    alignment: str = "center"  # left, center, right


class UIManager:
    """
    Manages UI elements and interactions.
    Composite pattern for UI hierarchy.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        self.theme_manager = theme_manager or ThemeManager()
        self.elements: Dict[str, UIElement] = {}
        self._element_layers: Dict[int, List[str]] = {}  # z-index layering

    def add_element(self, element: UIElement, layer: int = 0) -> None:
        """Add a UI element to the manager."""
        self.elements[element.element_id] = element

        if layer not in self._element_layers:
            self._element_layers[layer] = []
        self._element_layers[layer].append(element.element_id)

    def remove_element(self, element_id: str) -> None:
        """Remove a UI element."""
        if element_id in self.elements:
            del self.elements[element_id]

            # Remove from layers
            for layer_elements in self._element_layers.values():
                if element_id in layer_elements:
                    layer_elements.remove(element_id)

    def get_element(self, element_id: str) -> Optional[UIElement]:
        """Get an element by ID."""
        return self.elements.get(element_id)

    def handle_mouse_click(self, position: Tuple[int, int]) -> None:
        """Handle mouse click on UI elements."""
        # Check elements in reverse layer order (top to bottom)
        for layer in sorted(self._element_layers.keys(), reverse=True):
            for element_id in reversed(self._element_layers[layer]):
                element = self.elements.get(element_id)

                if not element or not element.visible or not element.interactive:
                    continue

                if element.contains_point(position):
                    if isinstance(element, Button):
                        element.handle_click()
                    return  # Stop after first hit

    def handle_mouse_move(self, position: Tuple[int, int]) -> None:
        """Handle mouse movement for hover effects."""
        for element in self.elements.values():
            if isinstance(element, Button) and element.visible:
                element.is_hovered = element.contains_point(position)

    def update(self, dt: float) -> None:
        """Update UI elements (for animations, etc.)."""
        # Can be extended for animated UI elements
        pass

    def get_elements_to_render(self) -> List[UIElement]:
        """Get elements in render order (by layer)."""
        result = []
        for layer in sorted(self._element_layers.keys()):
            for element_id in self._element_layers[layer]:
                element = self.elements.get(element_id)
                if element and element.visible:
                    result.append(element)
        return result

    def create_game_ui(self, screen_width: int, screen_height: int) -> None:
        """Create standard game UI elements."""
        # Score label
        score_label = Label(
            element_id="score_label",
            position=(20, 20),
            size=(200, 40),
            text="Score: 0",
            font_size=24
        )
        self.add_element(score_label, layer=10)

        # Timer label
        timer_label = Label(
            element_id="timer_label",
            position=(screen_width - 220, 20),
            size=(200, 40),
            text="Time: 0:00",
            font_size=24
        )
        self.add_element(timer_label, layer=10)

        # Progress bar
        progress_bar = ProgressBar(
            element_id="progress_bar",
            position=(20, screen_height - 60),
            size=(screen_width - 40, 40),
            current_value=0,
            max_value=100
        )
        self.add_element(progress_bar, layer=10)

        # Pause button
        pause_button = Button(
            element_id="pause_button",
            position=(screen_width // 2 - 50, 20),
            size=(100, 40),
            text="Pause"
        )
        self.add_element(pause_button, layer=10)

    def update_score(self, score: float) -> None:
        """Update score display."""
        score_label = self.get_element("score_label")
        if isinstance(score_label, Label):
            score_label.text = f"Score: {score:.1f}"

    def update_timer(self, seconds: float) -> None:
        """Update timer display."""
        timer_label = self.get_element("timer_label")
        if isinstance(timer_label, Label):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            timer_label.text = f"Time: {minutes}:{secs:02d}"

    def update_progress(self, current: int, total: int) -> None:
        """Update progress bar."""
        progress_bar = self.get_element("progress_bar")
        if isinstance(progress_bar, ProgressBar):
            progress_bar.current_value = current
            progress_bar.max_value = total
