"""
Main entry point for the Cognitive Memory Game.
Demonstrates complete usage of the game system.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models.patient import Patient, PatientProfile, PatientInterest, InterestCategory
from models.game_content import GameContent, ContentItem, ContentCategory, ContentType
from models.game_state import GameDifficulty
from controllers.game_controller import GameController
from views.renderer import RenderConfig, PygameRenderer
from views.ui_manager import UIManager, ThemeManager
from views.ar_vr_interface import ARVRInterface, SpatialMode
from services.analytics import AnalyticsService
from services.data_persistence import DataPersistenceService
from config.game_config import ConfigurationManager


class MemoryGameApp:
    """Main application class coordinating all components."""

    def __init__(self):
        # Initialize configuration
        self.config_manager = ConfigurationManager()
        self.config_manager.load_config()
        self.config = self.config_manager.config

        # Initialize services
        self.persistence = DataPersistenceService(
            storage_backend="json",
            data_path=self.config.data_path
        )
        self.analytics = AnalyticsService()

        # Initialize content repository
        self.content_repository = GameContent()

        # Initialize patient profile manager
        self.patient_profile = PatientProfile()

        # Initialize game controller
        self.game_controller = GameController(self.content_repository)

        # Initialize UI components
        self.theme_manager = ThemeManager()
        self.ui_manager = UIManager(self.theme_manager)

        # Initialize renderer (will be set up later)
        self.renderer = None

        # AR/VR interface
        self.ar_vr = ARVRInterface(SpatialMode.TRADITIONAL_2D)

        # Current patient
        self.current_patient = None

        # Game loop control
        self.running = False

    def setup_sample_content(self):
        """Set up sample content for demonstration."""
        print("Setting up sample content...")

        # Create sample content items
        sample_content = [
            ContentItem(
                category=ContentCategory.FAMILY,
                content_type=ContentType.IMAGE,
                file_path="assets/images/family_photo1.jpg",
                title="Family Gathering",
                description="Summer family reunion",
                tags={"family", "summer", "happy"},
                emotional_valence="positive"
            ),
            ContentItem(
                category=ContentCategory.SPORTS,
                content_type=ContentType.IMAGE,
                file_path="assets/images/soccer.jpg",
                title="Soccer",
                description="Soccer ball",
                tags={"sports", "soccer", "outdoor"},
                emotional_valence="positive"
            ),
            ContentItem(
                category=ContentCategory.ART,
                content_type=ContentType.IMAGE,
                file_path="assets/images/painting.jpg",
                title="Beautiful Painting",
                description="Landscape painting",
                tags={"art", "painting", "landscape"},
                emotional_valence="positive"
            ),
            ContentItem(
                category=ContentCategory.NATURE,
                content_type=ContentType.IMAGE,
                file_path="assets/images/mountain.jpg",
                title="Mountain Vista",
                description="Beautiful mountain view",
                tags={"nature", "mountain", "scenic"},
                emotional_valence="positive"
            ),
            ContentItem(
                category=ContentCategory.MUSIC,
                content_type=ContentType.IMAGE,
                file_path="assets/images/piano.jpg",
                title="Piano",
                description="Grand piano",
                tags={"music", "piano", "instrument"},
                emotional_valence="neutral"
            ),
            ContentItem(
                category=ContentCategory.PETS,
                content_type=ContentType.IMAGE,
                file_path="assets/images/dog.jpg",
                title="Golden Retriever",
                description="Friendly dog",
                tags={"pets", "dog", "animal"},
                emotional_valence="positive"
            ),
            ContentItem(
                category=ContentCategory.FOOD,
                content_type=ContentType.IMAGE,
                file_path="assets/images/cake.jpg",
                title="Birthday Cake",
                description="Chocolate cake",
                tags={"food", "cake", "dessert"},
                emotional_valence="positive"
            ),
            ContentItem(
                category=ContentCategory.TRAVEL,
                content_type=ContentType.IMAGE,
                file_path="assets/images/beach.jpg",
                title="Beach Paradise",
                description="Tropical beach",
                tags={"travel", "beach", "vacation"},
                emotional_valence="positive"
            ),
        ]

        for content in sample_content:
            self.content_repository.add_content(content)

        print(f"Added {len(sample_content)} content items")

    def create_sample_patient(self) -> Patient:
        """Create a sample patient profile."""
        print("Creating sample patient...")

        # Create patient
        patient = self.patient_profile.create_patient(
            name="John Doe",
            age=75
        )

        # Add interests
        interests = [
            PatientInterest(
                category=InterestCategory.SPORTS,
                name="Soccer",
                importance=8,
                notes="Played soccer for 30 years"
            ),
            PatientInterest(
                category=InterestCategory.FAMILY,
                name="Grandchildren",
                importance=10,
                notes="Loves spending time with grandchildren"
            ),
            PatientInterest(
                category=InterestCategory.NATURE,
                name="Hiking",
                importance=7,
                notes="Enjoys mountain hiking"
            ),
            PatientInterest(
                category=InterestCategory.MUSIC,
                name="Piano",
                importance=6,
                notes="Plays piano as a hobby"
            ),
        ]

        for interest in interests:
            patient.add_interest(interest)

        # Configure accessibility
        patient.accessibility.font_size = "large"
        patient.accessibility.audio_cues = True

        print(f"Created patient: {patient.name} (ID: {patient.patient_id})")
        return patient

    def setup_renderer(self):
        """Initialize the game renderer."""
        print("Initializing renderer...")

        # Create render config from game config
        render_config = RenderConfig(
            width=self.config.window_width,
            height=self.config.window_height,
            fullscreen=self.config.fullscreen,
            enable_animations=self.config.enable_animations
        )

        # Adjust for accessibility if needed
        if self.current_patient:
            render_config.adjust_for_accessibility(
                self.current_patient.accessibility.to_dict()
            )

        # Create Pygame renderer
        try:
            self.renderer = PygameRenderer(render_config)
            self.renderer.initialize()
            print("Renderer initialized successfully")
            return True
        except RuntimeError as e:
            print(f"Failed to initialize renderer: {e}")
            print("Running in headless mode (no graphics)")
            return False

    def setup_game(self, difficulty: GameDifficulty = GameDifficulty.MEDIUM):
        """Set up a new game."""
        if not self.current_patient:
            print("Error: No patient selected")
            return False

        print(f"Setting up game with difficulty: {difficulty.value}")

        # Set up game using controller
        self.game_controller.setup_game(
            patient=self.current_patient,
            difficulty=difficulty,
            use_personalized_content=True
        )

        # Subscribe to game events
        self.game_controller.subscribe('game_started', self.on_game_started)
        self.game_controller.subscribe('card_flipped', self.on_card_flipped)
        self.game_controller.subscribe('match_found', self.on_match_found)
        self.game_controller.subscribe('match_failed', self.on_match_failed)
        self.game_controller.subscribe('game_ended', self.on_game_ended)

        print("Game setup complete")
        return True

    # Event handlers
    def on_game_started(self, event):
        """Handle game start event."""
        print(f"Game started: {event.data['game_id']}")

    def on_card_flipped(self, event):
        """Handle card flip event."""
        print(f"Card flipped: {event.data['card_id']}")
        # Play sound effect if enabled
        if self.config.enable_audio and self.renderer:
            self.renderer.play_sound('card_flip')

    def on_match_found(self, event):
        """Handle match found event."""
        print(f"Match found! Cards: {event.data['card_ids']}")
        if self.config.enable_audio and self.renderer:
            self.renderer.play_sound('match_success')

    def on_match_failed(self, event):
        """Handle match failed event."""
        print(f"No match. Cards: {event.data['card_ids']}")

    def on_game_ended(self, event):
        """Handle game end event."""
        print("Game ended!")
        print(f"Final score: {event.data.get('metrics', {}).get('memory_score', 0):.1f}")

        # Analyze and save results
        self.analyze_session()

    def play_game_headless(self):
        """Play game in headless mode (no graphics, for testing)."""
        print("\n=== Playing game in headless mode ===")

        # Start the game
        self.game_controller.start_game()

        # Simulate gameplay
        cards = self.game_controller.get_all_cards()
        card_ids = [card.card_id for card in cards]

        import random
        random.shuffle(card_ids)

        # Flip cards in pairs
        for i in range(0, len(card_ids), 2):
            if i + 1 >= len(card_ids):
                break

            card1_id = card_ids[i]
            card2_id = card_ids[i + 1]

            print(f"\nFlipping card {i // 2 + 1}/{len(card_ids) // 2}")

            # Flip first card
            result1 = self.game_controller.flip_card(card1_id)
            if result1['success']:
                print(f"  Card 1 revealed")

            # Flip second card
            result2 = self.game_controller.flip_card(card2_id)
            if result2['success']:
                print(f"  Card 2 revealed")

                if result2.get('is_match'):
                    print("  ✓ MATCH!")
                else:
                    print("  ✗ No match")
                    # Flip cards back down
                    import time
                    time.sleep(0.5)
                    self.game_controller.flip_cards_down()

            # Check if game is complete
            if result2.get('game_complete'):
                print("\n=== GAME COMPLETE ===")
                break

        # Get final results
        progress = self.game_controller.get_progress()
        print(f"\nFinal Progress:")
        print(f"  Matched: {progress['matched_pairs']}/{progress['total_pairs']}")
        print(f"  Score: {progress['current_score']:.1f}")
        print(f"  Moves: {progress['moves']}")

    def analyze_session(self):
        """Analyze the completed game session."""
        game_state = self.game_controller.get_game_state()

        if not game_state:
            return

        # Record session
        self.analytics.record_session(
            self.current_patient.patient_id,
            game_state
        )

        # Analyze
        insights = self.analytics.analyze_session(game_state)

        print("\n=== Cognitive Insights ===")
        for insight in insights:
            print(f"\n{insight.title} ({insight.category})")
            print(f"  {insight.description}")
            print(f"  Confidence: {insight.confidence * 100:.0f}%")

        # Save game state
        self.persistence.save_game_state(game_state)

        # Save updated patient profile
        self.persistence.save_patient(self.current_patient)

    def generate_report(self):
        """Generate progress report for current patient."""
        if not self.current_patient:
            print("No patient selected")
            return

        report = self.analytics.get_progress_report(
            self.current_patient,
            days=30
        )

        print("\n=== Progress Report ===")
        print(f"Patient: {report['patient_name']}")
        print(f"Sessions: {report['total_sessions']}")
        print(f"\nOverall Statistics:")
        stats = report['overall_statistics']
        print(f"  Average Memory Score: {stats['average_memory_score']:.1f}")
        print(f"  Average Accuracy: {stats['average_accuracy'] * 100:.1f}%")

        print(f"\nTrends:")
        for metric, trend_data in report['trends'].items():
            print(f"  {metric}: {trend_data['trend_direction']}")

        if report.get('recommendations'):
            print(f"\nRecommendations:")
            for rec in report['recommendations']:
                print(f"  - {rec}")

    def run(self):
        """Run the application."""
        print("=== Cognitive Memory Game ===\n")

        # Setup
        self.setup_sample_content()
        self.current_patient = self.create_sample_patient()

        # Try to initialize graphics
        has_graphics = self.setup_renderer()

        # Set up a game
        self.setup_game(GameDifficulty.EASY)

        if not has_graphics:
            # Run in headless mode
            self.play_game_headless()
        else:
            print("\nGraphics mode would start here")
            print("Simulating gameplay instead...")
            self.play_game_headless()

        # Generate report
        self.generate_report()

        print("\n=== Application Complete ===")


def main():
    """Main entry point."""
    app = MemoryGameApp()
    app.run()


if __name__ == "__main__":
    main()
