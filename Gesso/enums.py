from enum import Enum, auto

class ToolType(Enum):
    NONE = auto()
    
    # --- NAVIGATION ---
    MOVE = auto()       # (V) Move layer
    PAN = auto()        # (H or Space) Pan view
    ZOOM = auto()       # (Z) Zoom
    
    # --- SELECTION ---
    MARQUEE = auto()    # (M) Rectangular selection
    LASSO = auto()      # (L) Freehand selection (Placeholder)
    MAGIC_WAND = auto() # (W) Magic Wand (Placeholder)
    
    # --- CREATION ---
    BRUSH = auto()      # (B) Paint
    ERASER = auto()     # (E) Erase
    FILL = auto()       # (G) Bucket Fill
    EYEDROPPER = auto() # (I) Pick color
    
    # --- MANIPULATION ---
    SCALE = auto()      # (Shift+T) Transform