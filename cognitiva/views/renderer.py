"""
Rendering system for the memory game.
Abstract rendering layer to support multiple backends (Pygame, PyQt, Web, AR/VR).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json

from ..models.card import Card, CardState
from ..models.game_content import ContentItem, ContentType


@dataclass
class RenderConfig:
    """Configuration for the renderer."""
    # Screen/Window settings
    width: int = 1920
    height: int = 1080
    fullscreen: bool = False

    # Grid settings
    card_width: int = 150
    card_height: int = 200
    card_spacing: int = 20
    grid_offset_x: int = 100
    grid_offset_y: int = 150

    # Animation settings
    flip_animation_duration: float = 0.5
    match_animation_duration: float = 0.8
    shuffle_animation_duration: float = 1.0
    enable_animations: bool = True

    # Visual settings
    show_grid_lines: bool = False
    show_card_borders: bool = True
    border_width: int = 2
    corner_radius: int = 10

    # Colors (RGB tuples)
    background_color: Tuple[int, int, int] = (245, 245, 250)
    card_back_color: Tuple[int, int, int] = (100, 120, 180)
    card_front_color: Tuple[int, int, int] = (255, 255, 255)
    border_color: Tuple[int, int, int] = (80, 100, 160)
    matched_overlay_color: Tuple[int, int, int, int] = (100, 200, 100, 100)  # RGBA

    # Font settings
    font_family: str = "Arial"
    title_font_size: int = 48
    info_font_size: int = 24

    # Accessibility
    high_contrast: bool = False
    colorblind_mode: Optional[str] = None

    def adjust_for_accessibility(self, accessibility_settings: Dict) -> None:
        """Adjust render config based on accessibility settings."""
        if accessibility_settings.get('high_contrast'):
            self.high_contrast = True
            self.background_color = (0, 0, 0)
            self.card_front_color = (255, 255, 255)
            self.border_width = 4

        if accessibility_settings.get('color_blind_mode'):
            self.colorblind_mode = accessibility_settings['color_blind_mode']
            # Adjust colors for colorblind modes
            if self.colorblind_mode == 'protanopia':
                self.card_back_color = (0, 120, 180)
            elif self.colorblind_mode == 'deuteranopia':
                self.card_back_color = (180, 80, 0)


class GameRenderer(ABC):
    """
    Abstract base class for game renderers.
    Template Method pattern - defines rendering pipeline.
    """

    def __init__(self, config: RenderConfig):
        self.config = config
        self._resources: Dict[str, Any] = {}
        self._loaded = False

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the renderer and graphics system."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Clean up renderer resources."""
        pass

    @abstractmethod
    def load_image(self, path: str) -> Any:
        """Load an image resource."""
        pass

    @abstractmethod
    def load_sound(self, path: str) -> Any:
        """Load a sound resource."""
        pass

    @abstractmethod
    def clear_screen(self) -> None:
        """Clear the screen/canvas."""
        pass

    @abstractmethod
    def render_card(self, card: Card, content: Optional[ContentItem],
                   position: Tuple[int, int], animation_state: Dict) -> None:
        """Render a single card."""
        pass

    @abstractmethod
    def render_text(self, text: str, position: Tuple[int, int],
                   font_size: int, color: Tuple[int, int, int]) -> None:
        """Render text at a position."""
        pass

    @abstractmethod
    def render_ui_panel(self, position: Tuple[int, int],
                       size: Tuple[int, int], content: Dict) -> None:
        """Render a UI panel with information."""
        pass

    @abstractmethod
    def present(self) -> None:
        """Present/flip the rendered frame."""
        pass

    @abstractmethod
    def play_sound(self, sound_id: str) -> None:
        """Play a sound effect."""
        pass

    # Template method - defines the rendering pipeline
    def render_frame(self, cards: List[Card], content_map: Dict[str, ContentItem],
                    ui_data: Dict, animation_states: Dict[str, Dict]) -> None:
        """
        Main rendering method. Template pattern.
        Subclasses override individual rendering methods.
        """
        self.clear_screen()
        self.render_background()
        self.render_cards(cards, content_map, animation_states)
        self.render_ui(ui_data)
        self.present()

    def render_background(self) -> None:
        """Render the background. Can be overridden."""
        pass

    def render_cards(self, cards: List[Card], content_map: Dict[str, ContentItem],
                    animation_states: Dict[str, Dict]) -> None:
        """Render all cards."""
        for card in cards:
            # Calculate screen position from grid position
            screen_pos = self.grid_to_screen_position(card.position)

            # Get content if card is face up
            content = None
            if card.state != CardState.FACE_DOWN:
                content = content_map.get(card.content_id)

            # Get animation state for this card
            anim_state = animation_states.get(card.card_id, {})

            self.render_card(card, content, screen_pos, anim_state)

    def render_ui(self, ui_data: Dict) -> None:
        """Render UI elements."""
        # Title
        if 'title' in ui_data:
            self.render_text(
                ui_data['title'],
                (self.config.width // 2, 50),
                self.config.title_font_size,
                (50, 50, 50)
            )

        # Score panel
        if 'score' in ui_data:
            self.render_ui_panel(
                (20, 20),
                (300, 100),
                {'score': ui_data['score']}
            )

        # Time panel
        if 'time' in ui_data:
            self.render_ui_panel(
                (self.config.width - 320, 20),
                (300, 100),
                {'time': ui_data['time']}
            )

    def grid_to_screen_position(self, grid_pos: Tuple[int, int]) -> Tuple[int, int]:
        """Convert grid position to screen coordinates."""
        row, col = grid_pos
        x = self.config.grid_offset_x + col * (self.config.card_width + self.config.card_spacing)
        y = self.config.grid_offset_y + row * (self.config.card_height + self.config.card_spacing)
        return (x, y)

    def load_content_resource(self, content: ContentItem) -> Any:
        """Load a content resource (image, sound, etc.)."""
        if content.content_id in self._resources:
            return self._resources[content.content_id]

        resource = None
        if content.content_type == ContentType.IMAGE:
            resource = self.load_image(content.file_path)
        elif content.content_type == ContentType.AUDIO:
            resource = self.load_sound(content.file_path)
        # Add more types as needed

        if resource:
            self._resources[content.content_id] = resource

        return resource

    def preload_content(self, content_items: List[ContentItem]) -> None:
        """Preload all content resources."""
        for content in content_items:
            self.load_content_resource(content)


class PygameRenderer(GameRenderer):
    """
    Pygame-based renderer implementation.
    Concrete implementation of the GameRenderer.
    """

    def __init__(self, config: RenderConfig):
        super().__init__(config)
        self.screen = None
        self.clock = None
        self.fonts = {}

    def initialize(self) -> None:
        """Initialize Pygame."""
        try:
            import pygame
            pygame.init()

            flags = pygame.FULLSCREEN if self.config.fullscreen else 0
            self.screen = pygame.display.set_mode(
                (self.config.width, self.config.height),
                flags
            )
            pygame.display.set_caption("Cognitive Memory Game")

            self.clock = pygame.time.Clock()
            self._loaded = True

        except ImportError:
            raise RuntimeError("Pygame not installed. Install with: pip install pygame")

    def shutdown(self) -> None:
        """Shutdown Pygame."""
        import pygame
        pygame.quit()
        self._loaded = False

    def load_image(self, path: str) -> Any:
        """Load an image with Pygame."""
        import pygame
        try:
            image = pygame.image.load(path)
            # Scale to card size
            return pygame.transform.scale(
                image,
                (self.config.card_width - 20, self.config.card_height - 20)
            )
        except:
            # Return None if image can't be loaded
            return None

    def load_sound(self, path: str) -> Any:
        """Load a sound with Pygame."""
        import pygame
        try:
            return pygame.mixer.Sound(path)
        except:
            return None

    def clear_screen(self) -> None:
        """Clear the Pygame screen."""
        self.screen.fill(self.config.background_color)

    def render_card(self, card: Card, content: Optional[ContentItem],
                   position: Tuple[int, int], animation_state: Dict) -> None:
        """Render a card with Pygame."""
        import pygame

        x, y = position
        w, h = self.config.card_width, self.config.card_height

        # Create card rectangle
        card_rect = pygame.Rect(x, y, w, h)

        # Determine card color based on state
        if card.state == CardState.FACE_DOWN:
            color = self.config.card_back_color
        elif card.state == CardState.MATCHED:
            color = self.config.card_front_color
        else:
            color = self.config.card_front_color

        # Draw card background
        pygame.draw.rect(
            self.screen,
            color,
            card_rect,
            border_radius=self.config.corner_radius
        )

        # Draw card content if face up
        if card.state != CardState.FACE_DOWN and content:
            resource = self.load_content_resource(content)
            if resource:
                # Center the image on the card
                img_rect = resource.get_rect(center=card_rect.center)
                self.screen.blit(resource, img_rect)

        # Draw matched overlay
        if card.state == CardState.MATCHED:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill(self.config.matched_overlay_color)
            self.screen.blit(overlay, (x, y))

        # Draw border
        if self.config.show_card_borders:
            pygame.draw.rect(
                self.screen,
                self.config.border_color,
                card_rect,
                width=self.config.border_width,
                border_radius=self.config.corner_radius
            )

    def render_text(self, text: str, position: Tuple[int, int],
                   font_size: int, color: Tuple[int, int, int]) -> None:
        """Render text with Pygame."""
        import pygame

        if font_size not in self.fonts:
            self.fonts[font_size] = pygame.font.SysFont(
                self.config.font_family,
                font_size
            )

        font = self.fonts[font_size]
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect(center=position)
        self.screen.blit(text_surface, text_rect)

    def render_ui_panel(self, position: Tuple[int, int],
                       size: Tuple[int, int], content: Dict) -> None:
        """Render a UI panel with Pygame."""
        import pygame

        x, y = position
        w, h = size

        # Draw panel background
        panel_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            panel_rect,
            border_radius=10
        )
        pygame.draw.rect(
            self.screen,
            self.config.border_color,
            panel_rect,
            width=2,
            border_radius=10
        )

        # Render content
        y_offset = y + 20
        for key, value in content.items():
            text = f"{key.title()}: {value}"
            self.render_text(
                text,
                (x + w // 2, y_offset),
                self.config.info_font_size,
                (50, 50, 50)
            )
            y_offset += 30

    def present(self) -> None:
        """Present the frame."""
        import pygame
        pygame.display.flip()
        self.clock.tick(60)  # 60 FPS

    def play_sound(self, sound_id: str) -> None:
        """Play a sound effect."""
        if sound_id in self._resources:
            sound = self._resources[sound_id]
            if sound:
                sound.play()
