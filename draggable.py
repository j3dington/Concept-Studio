from PyQt6.QtWidgets import QFrame, QToolButton, QSlider, QWidget
from PyQt6.QtCore import Qt, QPoint

class DraggableFrame(QFrame):
    """A QFrame that can be dragged around the screen with the mouse."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.drag_start_offset = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.position().toPoint())
            
            if child and isinstance(child, (QToolButton, QSlider)):
                event.ignore()
                return
            self.drag_start_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            if self.drag_start_offset:
                new_pos = event.globalPosition().toPoint() - self.drag_start_offset
                self.move(new_pos)
                event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_start_offset = None