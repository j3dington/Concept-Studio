import os
from PyQt6.QtGui import QFontDatabase

def load_custom_font(font_filename):
    """
    Loads a font from assets/fonts/ and returns its real Family Name.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    font_path = os.path.join(base_path, "assets", "fonts", font_filename)
    
    if not os.path.exists(font_path):
        print(f"WARNING: Font file missing: {font_path}")
        return "Segoe UI" 

    font_id = QFontDatabase.addApplicationFont(font_path)
    
    if font_id == -1:
        print(f"WARNING: Failed to load font: {font_filename}")
        return "Segoe UI"
        
    family_names = QFontDatabase.applicationFontFamilies(font_id)
    return family_names[0] if family_names else "Segoe UI"