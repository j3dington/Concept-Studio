"""
Layer Class for Concept Studio

Represents a single drawing layer with:
- Image buffer (the actual pixel data)
- Transform properties (position, scale, rotation)
- Visibility and opacity
- Blend mode

"""

from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt


class Layer:
    """A single drawing layer with transform capabilities"""
    
    def __init__(self, name: str, width: int, height: int):
        """
        Initialize a new layer
        
        Args:
            name: Layer name (e.g., "Background", "Layer 1")
            width: Canvas width in pixels
            height: Canvas height in pixels
        """
        
        # Basic properties
        self.name = name
        self.visible = True
        self.opacity = 1.0  # 0.0 to 1.0
        self.blend_mode = "Normal"
        self.is_floating = False
        
        # Transform properties
        self.x = 0.0
        self.y = 0.0
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.rotation = 0.0
        
        # Image buffer - ARGB format
        # A+ NOTE: Premultiplied = Alpha is already applied to RGB
        # This makes blending faster!
        self.image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(Qt.GlobalColor.transparent)
    
    def get_memory_size(self) -> float:
        """
        Calculate memory usage in MB
        
        Total for 1920x1080:
        1920 × 1080 × 4 bytes = 8,294,400 bytes = ~8.3 MB per layer!
        
        Returns:
            float: Memory usage in megabytes
        """
        bytes_used = self.image.sizeInBytes()
        return bytes_used / (1024 * 1024)
    
    def __repr__(self):
        """String representation for debugging"""
        return f"Layer('{self.name}', visible={self.visible}, opacity={self.opacity:.2f})"
