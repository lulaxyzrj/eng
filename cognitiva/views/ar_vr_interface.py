"""
AR/VR Interface and Spatial Rendering.
Preparation layer for future AR/VR integration.
Supports spatial positioning, 3D transformations, and immersive interactions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import math


class SpatialMode(Enum):
    """Spatial rendering modes."""
    TRADITIONAL_2D = "2d"
    PSEUDO_3D = "pseudo_3d"  # 2D with depth effects
    STEREOSCOPIC = "stereoscopic"  # Side-by-side or top-bottom 3D
    VIRTUAL_REALITY = "vr"  # Full VR with head tracking
    AUGMENTED_REALITY = "ar"  # AR overlay on real world


@dataclass
class Vector3D:
    """3D vector for spatial positioning."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def distance_to(self, other: 'Vector3D') -> float:
        """Calculate distance to another point."""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    def normalize(self) -> 'Vector3D':
        """Return normalized vector."""
        length = math.sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
        if length == 0:
            return Vector3D(0, 0, 0)
        return Vector3D(self.x/length, self.y/length, self.z/length)

    def to_tuple(self) -> Tuple[float, float, float]:
        """Convert to tuple."""
        return (self.x, self.y, self.z)


@dataclass
class Quaternion:
    """Quaternion for 3D rotations (for VR head tracking)."""
    w: float = 1.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_euler(self) -> Tuple[float, float, float]:
        """Convert to Euler angles (pitch, yaw, roll) in degrees."""
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (self.w * self.x + self.y * self.z)
        cosr_cosp = 1 - 2 * (self.x * self.x + self.y * self.y)
        roll = math.atan2(sinr_cosp, cosr_cosp)

        # Pitch (y-axis rotation)
        sinp = 2 * (self.w * self.y - self.z * self.x)
        if abs(sinp) >= 1:
            pitch = math.copysign(math.pi / 2, sinp)
        else:
            pitch = math.asin(sinp)

        # Yaw (z-axis rotation)
        siny_cosp = 2 * (self.w * self.z + self.x * self.y)
        cosy_cosp = 1 - 2 * (self.y * self.y + self.z * self.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)

        return (math.degrees(pitch), math.degrees(yaw), math.degrees(roll))


@dataclass
class SpatialTransform:
    """Complete 3D transformation."""
    position: Vector3D = field(default_factory=Vector3D)
    rotation: Quaternion = field(default_factory=Quaternion)
    scale: Vector3D = field(default_factory=lambda: Vector3D(1, 1, 1))


@dataclass
class CardSpatialData:
    """Spatial data for a card in 3D space."""
    card_id: str
    transform: SpatialTransform = field(default_factory=SpatialTransform)

    # AR/VR specific
    is_anchored: bool = False  # Anchored to real-world surface (AR)
    anchor_id: Optional[str] = None

    # Interactive zones
    interaction_distance: float = 2.0  # meters
    gaze_activated: bool = False  # Can be selected by looking at it

    def is_in_interaction_range(self, viewer_position: Vector3D) -> bool:
        """Check if card is within interaction range."""
        distance = self.transform.position.distance_to(viewer_position)
        return distance <= self.interaction_distance


@dataclass
class VRController:
    """VR controller state."""
    controller_id: str
    position: Vector3D = field(default_factory=Vector3D)
    rotation: Quaternion = field(default_factory=Quaternion)

    # Button states
    trigger_pressed: bool = False
    grip_pressed: bool = False
    touchpad_touched: bool = False
    touchpad_position: Tuple[float, float] = (0.0, 0.0)

    # Haptic feedback
    haptic_intensity: float = 0.0  # 0.0 to 1.0


@dataclass
class VRHeadset:
    """VR headset tracking data."""
    position: Vector3D = field(default_factory=Vector3D)
    rotation: Quaternion = field(default_factory=Quaternion)

    # Eye tracking (for advanced VR headsets)
    left_eye_gaze: Optional[Vector3D] = None
    right_eye_gaze: Optional[Vector3D] = None
    combined_gaze: Optional[Vector3D] = None


@dataclass
class ARMarker:
    """AR marker/anchor in the real world."""
    marker_id: str
    position: Vector3D
    rotation: Quaternion
    confidence: float = 1.0  # 0.0 to 1.0, tracking confidence
    marker_type: str = "surface"  # surface, image, object


class SpatialRenderer(ABC):
    """
    Abstract base class for spatial rendering.
    Can be implemented for different platforms (Unity, Unreal, WebXR, ARCore, ARKit).
    """

    def __init__(self, mode: SpatialMode):
        self.mode = mode
        self.spatial_cards: Dict[str, CardSpatialData] = {}

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the spatial renderer."""
        pass

    @abstractmethod
    def render_card_3d(self, card_spatial_data: CardSpatialData,
                      content_data: Any) -> None:
        """Render a card in 3D space."""
        pass

    @abstractmethod
    def get_viewer_transform(self) -> SpatialTransform:
        """Get current viewer/camera transform."""
        pass

    @abstractmethod
    def raycast(self, origin: Vector3D, direction: Vector3D) -> Optional[str]:
        """
        Perform raycast to detect card hits.
        Returns card_id if hit, None otherwise.
        """
        pass

    def arrange_cards_in_circle(self, card_ids: List[str],
                               radius: float = 2.0,
                               height: float = 1.5) -> None:
        """
        Arrange cards in a circle around the viewer (good for VR).

        Args:
            card_ids: List of card IDs to arrange
            radius: Distance from center
            height: Height of the circle
        """
        num_cards = len(card_ids)
        angle_step = (2 * math.pi) / num_cards

        for i, card_id in enumerate(card_ids):
            angle = i * angle_step
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)

            # Create spatial data
            spatial_data = CardSpatialData(
                card_id=card_id,
                transform=SpatialTransform(
                    position=Vector3D(x, height, z)
                )
            )

            # Rotate card to face center
            # (simplified - real implementation would calculate proper rotation)

            self.spatial_cards[card_id] = spatial_data

    def arrange_cards_in_grid_3d(self, card_ids: List[str],
                                 rows: int, cols: int,
                                 spacing: float = 0.3) -> None:
        """
        Arrange cards in a 3D grid (can be curved for VR).

        Args:
            card_ids: List of card IDs
            rows: Number of rows
            cols: Number of columns
            spacing: Space between cards
        """
        idx = 0
        center_x = (cols - 1) * spacing / 2
        center_y = (rows - 1) * spacing / 2

        for row in range(rows):
            for col in range(cols):
                if idx >= len(card_ids):
                    break

                x = col * spacing - center_x
                y = row * spacing - center_y
                z = -2.0  # Distance from viewer

                spatial_data = CardSpatialData(
                    card_id=card_ids[idx],
                    transform=SpatialTransform(
                        position=Vector3D(x, y, z)
                    )
                )

                self.spatial_cards[card_ids[idx]] = spatial_data
                idx += 1

    def get_cards_in_view(self, viewer_transform: SpatialTransform,
                         field_of_view: float = 90.0) -> List[str]:
        """
        Get cards currently in the viewer's field of view.

        Args:
            viewer_transform: Current viewer position and rotation
            field_of_view: FOV in degrees

        Returns:
            List of card IDs in view
        """
        # Simplified implementation
        # Real implementation would use proper frustum culling
        in_view = []

        for card_id, spatial_data in self.spatial_cards.items():
            # Calculate if card is in front of viewer
            # This is a simplified check
            distance = spatial_data.transform.position.distance_to(
                viewer_transform.position
            )

            if distance <= 10.0:  # Within 10 meters
                in_view.append(card_id)

        return in_view


class ARVRInterface:
    """
    High-level interface for AR/VR functionality.
    Facade pattern to simplify AR/VR integration.
    """

    def __init__(self, mode: SpatialMode = SpatialMode.TRADITIONAL_2D):
        self.mode = mode
        self.spatial_renderer: Optional[SpatialRenderer] = None

        # VR specific
        self.headset: Optional[VRHeadset] = None
        self.controllers: Dict[str, VRController] = {}

        # AR specific
        self.ar_markers: Dict[str, ARMarker] = {}
        self.camera_transform: Optional[SpatialTransform] = None

    def initialize(self, mode: SpatialMode) -> bool:
        """
        Initialize AR/VR system.

        Returns:
            True if initialization successful
        """
        self.mode = mode

        if mode == SpatialMode.VIRTUAL_REALITY:
            return self._init_vr()
        elif mode == SpatialMode.AUGMENTED_REALITY:
            return self._init_ar()

        return True

    def _init_vr(self) -> bool:
        """Initialize VR system (placeholder for future integration)."""
        # This would integrate with SteamVR, Oculus SDK, OpenXR, etc.
        # For now, create mock data
        self.headset = VRHeadset()
        self.controllers["left"] = VRController(controller_id="left")
        self.controllers["right"] = VRController(controller_id="right")
        return True

    def _init_ar(self) -> bool:
        """Initialize AR system (placeholder for future integration)."""
        # This would integrate with ARCore, ARKit, etc.
        self.camera_transform = SpatialTransform()
        return True

    def update_tracking(self) -> None:
        """Update tracking data from VR/AR system."""
        if self.mode == SpatialMode.VIRTUAL_REALITY:
            self._update_vr_tracking()
        elif self.mode == SpatialMode.AUGMENTED_REALITY:
            self._update_ar_tracking()

    def _update_vr_tracking(self) -> None:
        """Update VR headset and controller tracking."""
        # Placeholder - would read from VR SDK
        pass

    def _update_ar_tracking(self) -> None:
        """Update AR camera and marker tracking."""
        # Placeholder - would read from AR SDK
        pass

    def detect_card_interaction(self) -> Optional[str]:
        """
        Detect which card the user is interacting with.

        Returns:
            Card ID if interacting, None otherwise
        """
        if self.mode == SpatialMode.VIRTUAL_REALITY:
            return self._detect_vr_interaction()
        elif self.mode == SpatialMode.AUGMENTED_REALITY:
            return self._detect_ar_interaction()

        return None

    def _detect_vr_interaction(self) -> Optional[str]:
        """Detect VR interaction via controller pointing or gaze."""
        # Check if trigger is pressed on either controller
        for controller in self.controllers.values():
            if controller.trigger_pressed and self.spatial_renderer:
                # Perform raycast from controller
                direction = Vector3D(0, 0, -1)  # Forward direction
                card_id = self.spatial_renderer.raycast(
                    controller.position,
                    direction
                )
                if card_id:
                    return card_id

        # Check gaze interaction
        if self.headset and self.headset.combined_gaze and self.spatial_renderer:
            card_id = self.spatial_renderer.raycast(
                self.headset.position,
                self.headset.combined_gaze
            )
            if card_id:
                return card_id

        return None

    def _detect_ar_interaction(self) -> Optional[str]:
        """Detect AR interaction via screen tap or gesture."""
        # Placeholder - would process touch/gesture input
        # and raycast into AR scene
        return None

    def trigger_haptic_feedback(self, intensity: float = 0.5,
                                duration: float = 0.1) -> None:
        """
        Trigger haptic feedback on VR controllers.

        Args:
            intensity: Vibration intensity (0.0 to 1.0)
            duration: Duration in seconds
        """
        if self.mode == SpatialMode.VIRTUAL_REALITY:
            for controller in self.controllers.values():
                controller.haptic_intensity = intensity
                # Would trigger actual haptic feedback via VR SDK

    def place_card_at_marker(self, card_id: str, marker_id: str) -> bool:
        """
        Place a card at an AR marker position.

        Args:
            card_id: Card to place
            marker_id: AR marker to anchor to

        Returns:
            True if successful
        """
        if marker_id not in self.ar_markers or not self.spatial_renderer:
            return False

        marker = self.ar_markers[marker_id]

        spatial_data = CardSpatialData(
            card_id=card_id,
            transform=SpatialTransform(
                position=marker.position,
                rotation=marker.rotation
            ),
            is_anchored=True,
            anchor_id=marker_id
        )

        self.spatial_renderer.spatial_cards[card_id] = spatial_data
        return True

    def get_recommended_layout(self) -> str:
        """
        Get recommended card layout for current mode.

        Returns:
            Layout type name
        """
        layouts = {
            SpatialMode.TRADITIONAL_2D: "grid",
            SpatialMode.PSEUDO_3D: "curved_grid",
            SpatialMode.STEREOSCOPIC: "depth_grid",
            SpatialMode.VIRTUAL_REALITY: "circular_3d",
            SpatialMode.AUGMENTED_REALITY: "table_surface"
        }

        return layouts.get(self.mode, "grid")

    def supports_hand_tracking(self) -> bool:
        """Check if hand tracking is supported."""
        # Would check VR/AR system capabilities
        return self.mode == SpatialMode.VIRTUAL_REALITY

    def supports_eye_tracking(self) -> bool:
        """Check if eye tracking is supported."""
        # Would check VR headset capabilities
        return False  # Placeholder
