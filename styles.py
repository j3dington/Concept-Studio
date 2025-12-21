def get_stylesheet(base_color="#FFFFFF", text_color="#ca6e3e", accent_color="#ca6e3e", header_font="Segoe UI", body_font="Segoe UI"):
    """
    The 'Modern Business Card' Aesthetic.
    - Tighter radiuses (12px instead of 30px) for a more technical feel.
    - High letter-spacing on headers (Editorial look).
    - Subtle borders that look like expensive cardstock.
    """
    return f"""
    /* --- 1. GLOBAL TYPOGRAPHY --- */
    QWidget {{
        font-family: '{body_font}', 'Segoe UI', sans-serif;
        color: {text_color};
        selection-background-color: {accent_color};
        selection-color: white;
    }}

    /* --- 2. THE DESK (Canvas Background) --- */
    QWidget#Canvas {{
        background-color: #F0F0F0; /* Slightly cooler grey, like a gallery wall */
    }}

    /* --- 3. THE PANELS (The "Business Cards") --- */
    QFrame#TheBag, QFrame#LayerPanel, QFrame#BrushStudio {{
        background-color: {base_color};
        border: 1px solid #D6D6D6;
        border-radius: 16px; 
    }}

    /* --- 4. HEADERS & LABELS (The "Brand") --- */
    /* Applied to "SIZE", "OPACITY", "LAYERS" */
    QLabel {{
        font-family: '{header_font}';
        font-size: 8pt;
        font-weight: 800; /* Extra Bold */
        color: #999999;   /* Muted Silver */
        letter-spacing: 2px; /* Wide tracking = Expensive feel */
        text-transform: uppercase;
        margin-bottom: 2px;
    }}

    /* --- 5. TOOL BUTTONS (Icons) --- */
    QToolButton {{
        background-color: transparent;
        border-radius: 8px; /* Soft Square (Squircle) instead of Circle */
        icon-size: 22px;
        color: #777777;
        margin: 2px;
    }}

    QToolButton:hover {{
        background-color: #F5F5F5; /* Very subtle hover */
        color: {text_color};
        border: 1px solid #E0E0E0;
    }}

    QToolButton:checked {{
        background-color: {text_color}; /* Solid Charcoal for active tool */
        color: #FFFFFF;
        border: none;
    }}
    
    /* SPECIAL: The Brush Shape Button ("SOFT") */
    /* Looks like a small pill tag */
    QToolButton[popupMode="1"] {{ 
        font-family: '{header_font}';
        font-weight: 700;
        background-color: #F2F2F2;
        border: 1px solid #E0E0E0;
        color: {text_color};
        border-radius: 4px;
        padding-left: 8px;
        padding-right: 8px;
        letter-spacing: 1px;
    }}
    QToolButton[popupMode="1"]:hover {{
        border: 1px solid {accent_color};
        color: {accent_color};
    }}

    /* --- 6. LAYER LIST (The Stack) --- */
    QListWidget {{
        background-color: transparent;
        border: none;
        outline: none;
    }}

    QListWidget::item {{
        background-color: transparent;
        color: {text_color};
        border-bottom: 1px solid #EEEEEE; /* Separator lines */
        padding: 10px 4px;
        margin: 0px 8px;
    }}

    QListWidget::item:selected {{
        background-color: transparent;
        color: {accent_color};
        font-weight: bold;
        border-bottom: 2px solid {accent_color}; /* Active underline */
    }}
    
    QListWidget::item:hover {{
        background-color: #FAFAFA;
    }}

    /* --- 7. SLIDERS (Minimalist) --- */
    QSlider::groove:horizontal {{
        border: none;
        height: 2px; /* Ultra thin line */
        background: #E0E0E0;
        border-radius: 1px;
    }}

    QSlider::handle:horizontal {{
        background: {text_color}; /* Sharp Black Dot */
        width: 10px;
        height: 10px;
        margin: -4px 0;
        border-radius: 5px; /* Perfect Circle */
        border: 2px solid {base_color}; /* White ring around it */
    }}
    QSlider::handle:horizontal:hover {{
        background: {accent_color};
        width: 12px;
        height: 12px;
        margin: -5px 0;
        border-radius: 6px;
    }}

    /* --- 8. MENUS (Popups) --- */
    QMenu {{
        background-color: {base_color};
        border: 1px solid #D6D6D6;
        font-family: '{body_font}';
        padding: 4px;
        border-radius: 8px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
        color: {text_color};
    }}
    QMenu::item:selected {{
        background-color: {text_color}; /* Invert colors on hover */
        color: white;
    }}
    
    /* --- 9. SMALL ACTION BUTTONS (Layer Panel) --- */
    QPushButton#SmallBtn {{
        background-color: #F8F8F8;
        border: 1px solid #E0E0E0;
        border-radius: 18px; /* Makes a 36px button a perfect circle */
        padding: 5px;
    }}

    QPushButton#SmallBtn:hover {{
        background-color: #FFFFFF;
        border: 1px solid {accent_color};
    }}

    QPushButton#SmallBtn:pressed {{
        background-color: #EEEEEE;
        border: 1px solid #CCCCCC;
    }}
    
    #SmallBtn {{
        background-color: transparent;
        border-radius: 20px;
    }}

    #SmallBtn:hover {{
        background-color: #e0e0e0; /* Highlight when hovering */
    }}
    """