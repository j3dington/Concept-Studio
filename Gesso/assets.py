import os
from PyQt6.QtGui import (QIcon, QPixmap, QPainter, QTransform,
QCursor, QPen, QColor, QRadialGradient, QFontDatabase)
from PyQt6.QtCore import Qt, QByteArray, QSize
from PyQt6.QtSvg import QSvgRenderer

# Define where your icons live
ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")

print(f"--- GESSO DEBUG: ICON FOLDER IS AT: {ICON_DIR} ---")

def make_pixmap(raw_svg, color_hex, size=32):
    """Core helper to turn SVG text into a colored Pixmap."""
    try:
        svg_xml = raw_svg.replace("#000000", "currentColor").replace("black", "currentColor")
        svg_xml = svg_xml.replace("currentColor", color_hex)
        svg_data = QByteArray(svg_xml.encode('utf-8'))
        renderer = QSvgRenderer(svg_data)
        if not renderer.isValid(): return None
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap
    except Exception as e:
        print(f"Error rendering pixmap: {e}")
        return None

def get_qicon(filename, custom_color=None):
    """The 'Bulletproof' Icon Loader for Gesso."""
    if not filename.endswith(".svg"): filename += ".svg"
    path = os.path.join(ICON_DIR, filename)
    if not os.path.exists(path):
        print(f"❌ Missing Icon File: {path}")
        return QIcon()
    try:
        with open(path, "r", encoding="utf-8") as f: raw_svg = f.read()
    except Exception as e: return QIcon()

    icon = QIcon()
    pix_off = make_pixmap(raw_svg, "#999999")
    pix_on  = make_pixmap(raw_svg, "#FFFFFF")

    if pix_off and pix_on:
        icon.addPixmap(pix_off, QIcon.Mode.Normal, QIcon.State.Off)
        icon.addPixmap(pix_off, QIcon.Mode.Active, QIcon.State.Off)
        icon.addPixmap(pix_off, QIcon.Mode.Selected, QIcon.State.Off)
        icon.addPixmap(pix_on, QIcon.Mode.Normal, QIcon.State.On)
        icon.addPixmap(pix_on, QIcon.Mode.Active, QIcon.State.On)
        icon.addPixmap(pix_on, QIcon.Mode.Selected, QIcon.State.On)
    return icon

def get_custom_cursor(filename, color="#2D2D2D", scale=1.0, rotation=0, hotspot=(0,0)):
    """The Universal Gesso Cursor Engine."""
    if not filename.endswith(".svg"): filename += ".svg"
    path = os.path.join(ICON_DIR, filename)
    if not os.path.exists(path): return Qt.CursorShape.ArrowCursor
    with open(path, "r", encoding="utf-8") as f:
        raw_svg = f.read().replace("currentColor", color).replace("#000000", color)
    svg_data = QByteArray(raw_svg.encode('utf-8'))
    renderer = QSvgRenderer(svg_data)
    
    canvas_size = 64
    pix = QPixmap(canvas_size, canvas_size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()

    transform = QTransform()
    transform.rotate(rotation)
    transform.scale(scale, scale)
    final_pix = pix.transformed(transform, Qt.TransformationMode.SmoothTransformation)
    return QCursor(final_pix, hotspot[0], hotspot[1])

def get_round_cursor(diameter):
    """Draws a circle cursor on the fly."""
    safe_diam = int(max(4, min(diameter, 128)))
    size = safe_diam + 4 
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QPen(Qt.GlobalColor.white, 2))
    painter.drawEllipse(2, 2, safe_diam, safe_diam)
    painter.setPen(QPen(Qt.GlobalColor.black, 1))
    painter.drawEllipse(2, 2, safe_diam, safe_diam)
    painter.end()
    center = size // 2
    return QCursor(pixmap, center, center)

# --- NEW: BRUSH TIP GENERATOR ---
def get_soft_brush_pixmap(size, color):
    """Generates a soft, fuzzy circle 'stamp' for the brush engine."""
    # Ensure size is an integer
    size = int(size)
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Create Radial Gradient (Center = Opaque, Edge = Transparent)
    gradient = QRadialGradient(size/2, size/2, size/2)
    
    c_opaque = QColor(color)
    c_opaque.setAlpha(255) 
    
    c_transparent = QColor(color)
    c_transparent.setAlpha(0) 
    
    gradient.setColorAt(0.0, c_opaque)
    gradient.setColorAt(1.0, c_transparent)
    
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.end()
    
    return pixmap

# --- CUSTOM BRUSH LOADER ---
BRUSH_DIR = os.path.join(os.path.dirname(__file__), "brushes")

def get_available_brushes():
    """Scans the brushes folder and returns a list of filenames."""
    if not os.path.exists(BRUSH_DIR):
        os.makedirs(BRUSH_DIR)
        return []
    
    files = [f for f in os.listdir(BRUSH_DIR) if f.endswith(('.png', '.svg', '.jpg'))]
    return sorted(files)

def load_custom_brush(filename, size, color):
    """
    Loads an image file, resizes it, and recolors it to match the brush color.
    """
    path = os.path.join(BRUSH_DIR, filename)
    if not os.path.exists(path):
        return None
    
    base_image = QPixmap(path)
    if base_image.isNull(): return None
    
    scaled = base_image.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    result = QPixmap(scaled.size())
    result.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRect(result.rect())
    
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
    
    painter.drawPixmap(0, 0, scaled)
    
    painter.end()
    return result

# --- assets.py (Add to bottom) ---

def create_outline_cursor(pixmap, size):
    """
    Takes a brush image, finds the edges, and creates a high-contrast cursor.
    """
    safe_size = int(min(size, 128))
    if safe_size < 1: safe_size = 1
    
    src = pixmap.scaled(safe_size, safe_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    
    cursor_size = safe_size + 4
    result = QPixmap(cursor_size, cursor_size)
    result.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    
    painter.setOpacity(0.5)
    tmp = src.mask()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(Qt.GlobalColor.black)
    
    painter.drawPixmap(0, 1, src)
    painter.drawPixmap(2, 1, src)
    painter.drawPixmap(1, 0, src)
    painter.drawPixmap(1, 2, src)
    
    painter.setOpacity(1.0)
    
    white_copy = QPixmap(src.size())
    white_copy.fill(Qt.GlobalColor.transparent)
    wp = QPainter(white_copy)
    wp.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    wp.drawPixmap(0, 0, src)
    wp.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    wp.fillRect(white_copy.rect(), Qt.GlobalColor.white)
    wp.end()
    
    painter.drawPixmap(1, 1, white_copy)
    
    painter.end()
    
    return QCursor(result, cursor_size // 2, cursor_size // 2)

# --- NEW: FONT LOADER ---
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

def load_custom_fonts(preferred_font=None):
    """
    Scans 'fonts' folder. Registers ALL fonts found.
    Returns the 'preferred_font' name if found, otherwise returns the first one found.
    """
    if not os.path.exists(FONT_DIR):
        os.makedirs(FONT_DIR)
        return "Segoe UI"
        
    files = [f for f in os.listdir(FONT_DIR) if f.endswith(('.ttf', '.otf'))]
    if not files: return "Segoe UI"
        
    first_detected = None
    target_detected = None
    
    for filename in files:
        path = os.path.join(FONT_DIR, filename)
        font_id = QFontDatabase.addApplicationFont(path)
        
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                real_name = families[0]
                print(f"✅ Loaded: '{real_name}'")
                if first_detected is None:
                    first_detected = real_name
                if preferred_font and preferred_font.lower() in real_name.lower():
                    target_detected = real_name

    if target_detected:
        print(f"🎯 Selected Target Font: {target_detected}")
        return target_detected
        
    if first_detected:
        print(f"⚠️ Target '{preferred_font}' not found. Using '{first_detected}' instead.")
        return first_detected
        
    return "Segoe UI"