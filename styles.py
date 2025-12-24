def get_stylesheet(base_color="#FFFFFF", text_color="#212121", accent_color="#FF6000", header_font="Inter", body_font="Segoe UI"):
    """
    The 'ArtStation Light' Aesthetic (Refactored).
    - Unified ID selectors for custom frames.
    - Consistent padding and margin for high-density UI.
    - Centralized accenting for interactive states.
    """
    return f"""
    /* --- 1. THE WINDOW SHELL (Integrated Frame) --- */
    #RootFrame {{
        background-color: #212121;
        border: 2px solid {accent_color};
        border-radius: 12px;
    }}

    #TitleBar {{
        background-color: #FFFFFF;
        border-bottom: 1px solid #E1E4E8;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }}

    #TitleBar QLabel {{
        color: {accent_color};
        font-family: '{header_font}';
        font-weight: 900;
        font-size: 10pt;
        letter-spacing: 2px;
    }}
    
    /* --- 2. GLOBAL TYPOGRAPHY --- */
    QWidget {{
        font-family: '{body_font}', 'Segoe UI', sans-serif;
        color: {text_color};
        selection-background-color: {accent_color};
        selection-color: white;
    }}

    /* --- 3. WORKSPACE COMPONENTS (Canvas & Panels) --- */
    QWidget#Canvas {{
        background-color: {text_color};
    }}

    QFrame#TheBag, QFrame#LayerPanel, QFrame#BrushStudio {{
        background-color: {base_color};
        border: 1px solid #E0E0E0;
        border-radius: 8px;
    }}

    QLabel {{
        font-family: '{header_font}';
        font-size: 9pt;
        font-weight: 600;
        color: #757575;
        letter-spacing: 0.5px; 
        text-transform: uppercase;
        margin-bottom: 2px;
    }}

    /* --- 4. TOOLBARS & MENUS (Integrated Top Row) --- */
    QMenuBar {{
        background-color: #FFFFFF;
        /* Reducing vertical padding from 5px/10px to 2px */
        padding: 2px 10px; 
        border-bottom: 1px solid #E1E4E8;
        font-family: '{body_font}';
        font-size: 9pt;
        font-weight: 500;
        color: #424242;
        /* Explicitly setting a small height */
        max-height: 25px;
    }}

    QMenuBar::item {{
        background: transparent;
        padding: 2px 8px; /* Tighter padding for the 'View' text */
        margin-right: 2px;
        border-radius: 4px;
    }}

    QMenuBar::item:selected {{
        background-color: #FFF5ED;
        color: {accent_color};
    }}

    QMenu {{
        background-color: #FFFFFF;
        border: 1px solid #D6D6D6;
        padding: 4px;
        border-radius: 8px;
    }}

    QMenu::item {{
        padding: 8px 25px 8px 20px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background-color: {accent_color};
        color: #FFFFFF;
    }}

    /* --- 5. INTERACTIVE TOOLS (Buttons & Sliders) --- */
    QToolButton {{
        background-color: transparent;
        border-radius: 6px;
        icon-size: 22px;
        color: #424242;
        margin: 2px;
    }}

    QToolButton:hover {{
        background-color: #F0F0F0;
        border: 1px solid #D6D6D6;
    }}

    QToolButton:checked {{
        background-color: {accent_color};
        color: #FFFFFF;
        border: none;
    }}
    
    /* Brush Shape Pill Button */
    QToolButton[popupMode="1"] {{ 
        font-weight: 700;
        background-color: #FAFAFA;
        border: 1px solid #D6D6D6;
        color: {text_color};
        border-radius: 12px;
        padding: 4px 12px;
    }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: #E0E0E0;
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: {accent_color};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
        border: 2px solid #FFFFFF;
    }}

    /* --- 6. LAYER PANEL LISTS --- */
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}

    QListWidget::item {{
        background-color: #FFFFFF;
        color: #424242;
        border-bottom: 1px solid #F0F0F0;
        padding: 12px 10px;
        margin: 2px 8px;
        border-radius: 4px;
    }}

    QListWidget::item:selected {{
        background-color: #FFF5ED;
        color: {accent_color};
        font-weight: 700;
        border-left: 4px solid {accent_color};
    }}

    /* --- 7. INPUTS & DROPDOWNS --- */
    QComboBox {{
        background-color: #FAFAFA;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 4px 10px;
        min-height: 25px;
        color: #424242;
    }}

    QComboBox:hover {{
        border: 1px solid {accent_color};
    }}
    """