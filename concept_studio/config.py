"""
Configuration and Constants for Concept Studio

"""

from PyQt6.QtGui import QPainter

# ==========================================
# 🎨 BLEND MODES
# ==========================================
BLEND_MODES = {
    "Normal": QPainter.CompositionMode.CompositionMode_SourceOver,
    "Multiply": QPainter.CompositionMode.CompositionMode_Multiply,
    "Screen": QPainter.CompositionMode.CompositionMode_Screen,
    "Overlay": QPainter.CompositionMode.CompositionMode_Overlay,
    "Darken": QPainter.CompositionMode.CompositionMode_Darken,
    "Lighten": QPainter.CompositionMode.CompositionMode_Lighten,
}

# ==========================================
# 🎨 UI STYLESHEET (CSS-like styling)
# ==========================================
STYLESHEET = """
QMainWindow { background-color: #1e1e1e; }
QWidget { font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #e0e0e0; }
QFrame#FloatingStation, QFrame#LayerPanel {
    background-color: rgba(30, 30, 30, 0.90);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
}
QPushButton {
    background-color: transparent;
    border-radius: 10px;
    padding: 6px;
    color: #b0b0b0;
    font-weight: 600;
    border: 1px solid transparent;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 0.1);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.05);
}
QPushButton:checked {
    background-color: rgba(184, 153, 95, 0.2);
    color: #d4af37;
    border: 1px solid #d4af37;
}
QPushButton#DangerBtn:hover {
    background-color: rgba(255, 80, 80, 0.2);
    color: #ff5050;
    border: 1px solid #ff5050;
}
QListWidget { background-color: transparent; border: none; outline: none; }
QListWidget::item { padding: 8px; margin: 2px 5px; border-radius: 8px; color: #888; }
QListWidget::item:selected {
    background-color: rgba(184, 153, 95, 0.15);
    color: #e0e0e0;
    border-left: 3px solid #d4af37;
}
QSlider::groove:vertical { background: #2d2d2d; width: 6px; border-radius: 3px; }
QSlider::handle:vertical { background: #d4af37; height: 14px; margin: 0 -4px; border-radius: 7px; }
"""

# ==========================================
# 📐 DEFAULT VALUES
# ==========================================
DEFAULT_CANVAS_WIDTH = 1920
DEFAULT_CANVAS_HEIGHT = 1080
DEFAULT_BRUSH_SIZE = 5
MAX_HISTORY = 20
