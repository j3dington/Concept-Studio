from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
import config_manager

THEME = config_manager.CONFIG['theme']

def apply_shadow(widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setXOffset(0)
    shadow.setYOffset(4)
    shadow.setColor(QColor(0, 0, 0, 30))
    widget.setGraphicsEffect(shadow)

def get_stylesheet():
    return f"""
    /* === GLOBAL RESET === */
    QWidget {{
        font-family: '{THEME['font_family_ui']}', sans-serif;
        font-size: {THEME['font_size']};
        color: {THEME['text_header']};
    }}

    /* === MAIN WINDOW === */
    QMainWindow {{
        background-color: {THEME['window_bg']};
    }}
    
    /* === DOCK WIDGETS (The Windows) === */
    QDockWidget {{
        border: none;
    }}
    
    QDockWidget::title {{
        background: {THEME['panel_bg']};
        padding: 6px;
        border-radius: 12px 12px 0px 0px; 
    }}

    /* === PANEL CONTENT (The Cards) === */
    QFrame#PanelContent {{
        background-color: {THEME['panel_bg']};
        border-radius: 0px 0px 12px 12px;
        border-bottom: 1px solid {THEME['border_color']};
    }}

    /* === BUTTONS === */
    QPushButton {{
        background-color: {THEME['btn_default']};
        color: {THEME['btn_text']};
        border-radius: 8px;
        padding: 8px;
        font-weight: 600;
        border: none;
    }}

    QPushButton:hover {{
        background-color: {THEME['btn_accent']};
        color: white;
    }}
    """