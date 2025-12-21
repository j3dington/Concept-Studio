"""
Reference Board Items - Images and Sticky Notes
These are the draggable objects that live on the reference board.
"""

from PyQt6.QtWidgets import QWidget, QTextEdit, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QFont, QImage
from PyQt6.QtCore import Qt, QRect, QPoint, QSize, pyqtSignal
import json
import base64


class ReferenceItem:
    """
    Base class for all items on the reference board.
    Similar to how Layer works in your main canvas.
    """
    def __init__(self, pos: QPoint, size: QSize):
        self.pos = pos              # Position on infinite canvas
        self.size = size            # Width and height
        self.selected = False       # Is this item selected?
        self.z_index = 0           # Drawing order (higher = on top)
        
    def rect(self) -> QRect:
        """Returns the bounding box of this item."""
        return QRect(self.pos, self.size)
    
    def contains(self, point: QPoint) -> bool:
        """Check if a point is inside this item."""
        return self.rect().contains(point)
    
    def draw(self, painter: QPainter, offset: QPoint):
        """Draw this item. Subclasses override this."""
        pass
    
    def to_dict(self):
        """Serialize to dictionary for saving."""
        return {
            "type": self.__class__.__name__,
            "pos": {"x": self.pos.x(), "y": self.pos.y()},
            "size": {"w": self.size.width(), "h": self.size.height()},
            "z_index": self.z_index
        }


class ImageItem(ReferenceItem):
    """
    An image reference - draggable picture on the board.
    This is what artists drop onto the canvas.
    """
    def __init__(self, pos: QPoint, image_path: str = None, pixmap: QPixmap = None):
        # Load image
        if pixmap:
            self.original_pixmap = pixmap
        elif image_path:
            self.original_pixmap = QPixmap(image_path)
        else:
            self.original_pixmap = QPixmap(200, 200)
            self.original_pixmap.fill(QColor("#CCCCCC"))
        
        # Start with original size (but cap at 1200px max)
        original_size = self.original_pixmap.size()
        if original_size.width() > 1200 or original_size.height() > 1200:
            # Scale down to fit within 1200x1200
            original_size = original_size.scaled(1200, 1200, Qt.AspectRatioMode.KeepAspectRatio)
        
        self.pixmap = self.original_pixmap.scaled(
            original_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Initialize with image size
        super().__init__(pos, self.pixmap.size())
        self.image_path = image_path
        
    def resize_to(self, new_size: QSize):
        """Resize the image to a new size while maintaining aspect ratio."""
        self.size = new_size
        self.pixmap = self.original_pixmap.scaled(
            new_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.size = self.pixmap.size()  # Update to actual scaled size
    
    def get_resize_handle(self, point: QPoint, offset: QPoint) -> str:
        """
        Check if point is over a resize handle.
        Returns: 'nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w', or None
        """
        if not self.selected:
            return None
        
        draw_pos = self.pos + offset
        rect = QRect(draw_pos, self.size)
        
        handle_size = 8
        margin = 12  # Click area around handle
        
        # Helper to check if point is near a position
        def near(pos, target_pos):
            return (abs(pos.x() - target_pos.x()) < margin and 
                    abs(pos.y() - target_pos.y()) < margin)
        
        # Corner handles
        if near(point, rect.topLeft()):
            return 'nw'
        if near(point, rect.topRight()):
            return 'ne'
        if near(point, rect.bottomLeft()):
            return 'sw'
        if near(point, rect.bottomRight()):
            return 'se'
        
        # Edge handles
        if near(point, QPoint(rect.center().x(), rect.top())):
            return 'n'
        if near(point, QPoint(rect.center().x(), rect.bottom())):
            return 's'
        if near(point, QPoint(rect.left(), rect.center().y())):
            return 'w'
        if near(point, QPoint(rect.right(), rect.center().y())):
            return 'e'
        
        return None
    
    def get_delete_button_rect(self, offset: QPoint) -> QRect:
        """Get the rect for the delete X button."""
        if not self.selected:
            return QRect()
        
        draw_pos = self.pos + offset
        button_size = 20
        x = draw_pos.x() + self.size.width() - button_size - 2
        y = draw_pos.y() + 2
        return QRect(x, y, button_size, button_size)
        
    def draw(self, painter: QPainter, offset: QPoint):
        """Draw the image with optional selection border."""
        draw_pos = self.pos + offset
        
        # Draw the image
        painter.drawPixmap(draw_pos, self.pixmap)
        
        # Draw selection border if selected
        if self.selected:
            painter.setPen(QPen(QColor("#FF6B35"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRect(draw_pos, self.size))
            
            # Draw resize handles
            handle_size = 8
            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(QPen(QColor("#FF6B35"), 2))
            
            rect = QRect(draw_pos, self.size)
            
            # Corner handles
            handles = [
                rect.topLeft(),           # NW
                rect.topRight(),          # NE
                rect.bottomLeft(),        # SW
                rect.bottomRight(),       # SE
                QPoint(rect.center().x(), rect.top()),      # N
                QPoint(rect.center().x(), rect.bottom()),   # S
                QPoint(rect.left(), rect.center().y()),     # W
                QPoint(rect.right(), rect.center().y()),    # E
            ]
            
            for handle_pos in handles:
                painter.drawRect(
                    handle_pos.x() - handle_size//2, 
                    handle_pos.y() - handle_size//2,
                    handle_size, 
                    handle_size
                )
            
            # Draw delete button (X in top-right corner)
            delete_rect = self.get_delete_button_rect(offset)
            painter.setBrush(QColor("#FF4444"))
            painter.setPen(QPen(QColor("#CC0000"), 2))
            painter.drawEllipse(delete_rect)
            
            # Draw X
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            margin = 5
            painter.drawLine(
                delete_rect.left() + margin, delete_rect.top() + margin,
                delete_rect.right() - margin, delete_rect.bottom() - margin
            )
            painter.drawLine(
                delete_rect.right() - margin, delete_rect.top() + margin,
                delete_rect.left() + margin, delete_rect.bottom() - margin
            )
    
    def to_dict(self):
        """Save image data."""
        data = super().to_dict()
        
        # Convert pixmap to base64 for storage
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        self.pixmap.save(buffer, "PNG")
        
        data["image_data"] = base64.b64encode(byte_array.data()).decode('utf-8')
        data["image_path"] = self.image_path
        return data
    
    @staticmethod
    def from_dict(data):
        """Load image from saved data."""
        pos = QPoint(data["pos"]["x"], data["pos"]["y"])
        
        # Decode base64 image
        image_data = base64.b64decode(data["image_data"])
        image = QImage()
        image.loadFromData(image_data)
        pixmap = QPixmap.fromImage(image)
        
        item = ImageItem(pos, pixmap=pixmap)
        item.image_path = data.get("image_path")
        item.z_index = data.get("z_index", 0)
        return item


class StickyNote(ReferenceItem):
    """
    A text note - like a post-it note on the board.
    Artists can write ideas, notes, or reminders.
    """
    # Available colors
    COLORS = {
        "yellow": "#FFF59D",
        "pink": "#F8BBD0",
        "blue": "#BBDEFB",
        "green": "#C8E6C9",
        "orange": "#FFE0B2"
    }
    
    def __init__(self, pos: QPoint, size: QSize = None, text: str = "", color: str = "yellow"):
        default_size = size or QSize(200, 150)
        super().__init__(pos, default_size)
        
        self.text = text
        self.color_name = color
        self.color = QColor(self.COLORS.get(color, self.COLORS["yellow"]))
        self.font = QFont("Segoe UI", 10)
        
    def set_color(self, color_name: str):
        """Change the note color."""
        if color_name in self.COLORS:
            self.color_name = color_name
            self.color = QColor(self.COLORS[color_name])
    
    def get_delete_button_rect(self, offset: QPoint) -> QRect:
        """Get the rect for the delete X button."""
        if not self.selected:
            return QRect()
        
        draw_pos = self.pos + offset
        button_size = 16
        x = draw_pos.x() + self.size.width() - button_size - 2
        y = draw_pos.y() + 2
        return QRect(x, y, button_size, button_size)
        
    def draw(self, painter: QPainter, offset: QPoint):
        """Draw the sticky note."""
        draw_pos = self.pos + offset
        rect = QRect(draw_pos, self.size)
        
        # Draw note background
        painter.setBrush(self.color)
        
        # Border color - darker version of the note color
        border_color = self.color.darker(120)
        painter.setPen(QPen(border_color, 2))
        painter.drawRect(rect)
        
        # Draw text
        painter.setFont(self.font)
        painter.setPen(QColor("#000000"))
        
        # Add padding
        text_rect = rect.adjusted(10, 10, -10, -10)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap, self.text)
        
        # Draw selection border if selected
        if self.selected:
            painter.setPen(QPen(QColor("#FF6B35"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)
            
            # Draw delete button (X in top-right corner)
            delete_rect = self.get_delete_button_rect(offset)
            painter.setBrush(QColor("#FF4444"))
            painter.setPen(QPen(QColor("#CC0000"), 2))
            painter.drawEllipse(delete_rect)
            
            # Draw X
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            margin = 4
            painter.drawLine(
                delete_rect.left() + margin, delete_rect.top() + margin,
                delete_rect.right() - margin, delete_rect.bottom() - margin
            )
            painter.drawLine(
                delete_rect.right() - margin, delete_rect.top() + margin,
                delete_rect.left() + margin, delete_rect.bottom() - margin
            )
    
    def to_dict(self):
        """Save note data."""
        data = super().to_dict()
        data["text"] = self.text
        data["color_name"] = self.color_name  # Save color name instead of hex
        return data
    
    @staticmethod
    def from_dict(data):
        """Load note from saved data."""
        pos = QPoint(data["pos"]["x"], data["pos"]["y"])
        size = QSize(data["size"]["w"], data["size"]["h"])
        
        note = StickyNote(
            pos, 
            size, 
            data["text"],
            data.get("color_name", "yellow")  # Default to yellow if not specified
        )
        note.z_index = data.get("z_index", 0)
        return note


# Import helper for Qt
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice