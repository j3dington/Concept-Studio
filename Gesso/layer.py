from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPixmap, QImage, QPainter, QColor
from PyQt6.QtCore import Qt, QSize, QBuffer, QIODevice
from PyQt6 import QtCore

class Layer:
    def __init__(self, name, size: QSize):
        self.name = name
        self.visible = True
        self.opacity = 1.0
        self.pixmap = QPixmap(size)
        self.pixmap.fill(Qt.GlobalColor.transparent)
        self.blend_mode = "Normal"

    def clear(self):
        """Wipes the layer clean."""
        self.pixmap.fill(Qt.GlobalColor.transparent)

    def to_data(self):
        """Converts the layer into a save-able dictionary."""
        # 1. Convert Pixmap -> Image -> Bytes
        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QIODevice.OpenModeFlag.ReadWrite)
        self.pixmap.save(buffer, "PNG")
        image_bytes = buffer.data().data() # Get the raw bytes
        
        return {
            "name": self.name,
            "visible": self.visible,
            "opacity": self.opacity,
            "image_data": image_bytes
        }

    @staticmethod
    def from_data(data):
        """Reconstructs a Layer from saved data."""
        # 1. Create a blank layer
        # We assume 100x100 initially; the Pixmap load will resize it correctly
        layer = Layer(data["name"], QSize(100, 100))
        layer.visible = data["visible"]
        layer.opacity = data["opacity"]
        
        # 2. Load the bytes back into a Pixmap
        img = QImage()
        img.loadFromData(data["image_data"])
        layer.pixmap = QPixmap.fromImage(img)
        
        return layer