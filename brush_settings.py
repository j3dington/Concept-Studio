import math
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QFrame)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap, QTransform
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QPointF

from assets import get_soft_brush_pixmap, load_custom_brush
from draggable import DraggableFrame

class ColorSwatch(QWidget):
    """
    A small circular widget that displays the current active color.
    This is what the Eyedropper updates!
    """
    def __init__(self, initial_color=QColor("#ca6e3e")):
        super().__init__()
        self.setFixedSize(30, 30)
        self.current_color = initial_color

    def set_color(self, color):
        """The 'Receiver' method for color signals."""
        self.current_color = color
        self.update() # Triggers paintEvent to redraw the circle

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw the main color circle
        painter.setBrush(self.current_color)
        painter.setPen(QPen(QColor("#D6D6D6"), 1)) # Subtle silver border
        painter.drawEllipse(2, 2, 26, 26)

class BrushPreviewWidget(QWidget):
    """
    The 'Scratchpad' area that shows what the brush stroke will look like.
    """
    def __init__(self):
        super().__init__()
        self.setFixedHeight(120)
        # Default State
        self.brush_size = 20
        self.brush_color = QColor("#000000") 
        self.brush_shape = "Soft"
        self.spacing = 10
        self.flow = .99
        
        # Jitter State
        self.jitter_size = 0.0
        self.jitter_angle = 0.0
        self.jitter_scatter = 0.0
        self.jitter_hue = 0.0
        
        self.setStyleSheet("background-color: #FFFFFF; border-radius: 8px; border: 1px solid #E0E0E0;")
        
    def set_color(self, color):
        """Updates the brush color used in the preview stroke."""
        self.brush_color = color
        self.update()

    def update_settings(self, size, shape, color, spacing, flow, j_size, j_angle, j_scatter, j_hue):
        self.brush_size = size
        self.brush_shape = shape
        self.brush_color = color
        self.spacing = max(1, spacing)
        self.flow = flow
        
        self.jitter_size = j_size
        self.jitter_angle = j_angle
        self.jitter_scatter = j_scatter
        self.jitter_hue = j_hue
        
        self.update() 

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        target_max_size = 50.0
        view_scale = 1.0
        if self.brush_size > target_max_size:
            view_scale = target_max_size / self.brush_size
            
        v_size = self.brush_size * view_scale
        v_spacing = self.spacing * view_scale
        
        if self.brush_shape == "Soft":
            base_tip = get_soft_brush_pixmap(int(v_size), self.brush_color)
        else:
            base_tip = load_custom_brush(self.brush_shape, int(v_size), self.brush_color)
            if not base_tip: 
                base_tip = get_soft_brush_pixmap(int(v_size), self.brush_color)
        
        width = self.width()
        height = self.height()
        mid_y = height / 2
        
        x = 20
        while x < width - 20:
            wave_height = 30 * (1.0 if view_scale == 1.0 else 0.5) 
            y = mid_y + (math.sin(x * 0.05) * wave_height)
            draw_pos = QPointF(x, y)
            
            if self.jitter_scatter > 0:
                scatter_radius = v_size * 2.0 * self.jitter_scatter
                dx = random.uniform(-scatter_radius, scatter_radius)
                dy = random.uniform(-scatter_radius, scatter_radius)
                draw_pos += QPointF(dx, dy)

            current_scale = 1.0
            if self.jitter_size > 0:
                current_scale = random.uniform(1.0 - self.jitter_size, 1.0)
            
            painter.setOpacity(self.flow)

            rotation = 0
            if self.jitter_angle > 0:
                rotation = random.uniform(0, 360) * self.jitter_angle
                
            current_tip = base_tip

            if self.jitter_hue > 0:
                h, s, v, a = self.brush_color.getHsv()
                shift = (random.random() - 0.5) * 360 * self.jitter_hue
                new_c = QColor.fromHsv(int((h + shift) % 360), max(50, s), v, a)
                
                tinted = QPixmap(base_tip.size())
                tinted.fill(Qt.GlobalColor.transparent)
                
                pt = QPainter(tinted)
                pt.drawPixmap(0, 0, base_tip)
                pt.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                pt.fillRect(tinted.rect(), new_c)
                pt.end()
                
                current_tip = tinted

            # --- DRAW TRANSFORMED ---
            transform = QTransform()
            transform.translate(draw_pos.x(), draw_pos.y())
            transform.rotate(rotation)
            transform.scale(current_scale, current_scale)
            
            painter.setTransform(transform)
            offset_x = current_tip.width() / 2
            offset_y = current_tip.height() / 2
            painter.drawPixmap(int(-offset_x), int(-offset_y), current_tip)
            painter.resetTransform()
            
            x += max(1, v_spacing)
            
        painter.end()

class BrushSettingsPanel(DraggableFrame):
    """
    The Floating UI Window. It acts as a 'Controller' for the Brush settings.
    """
    def __init__(self, canvas_ref):
        super().__init__()
        self.canvas = canvas_ref
        self.setObjectName("BrushStudio") 
        self.resize(280, 520) 
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5) 
        
        # --- HEADER SECTION (Title + Color Picker) ---
        header_row = QHBoxLayout()
        
        lbl_title = QLabel("BRUSH STUDIO")
        # Styling this to match your 'Modern Business Card' theme
        lbl_title.setStyleSheet("font-family: 'Segoe UI'; font-weight: 800; color: #999; letter-spacing: 2px; font-size: 10px;")
        
        # IMPORTANT: We name this 'color_picker' so main_window.py can find it!
        self.color_picker = ColorSwatch(self.canvas.brush_color) 
        
        header_row.addWidget(lbl_title)
        header_row.addStretch()
        header_row.addWidget(self.color_picker)
        
        layout.addLayout(header_row)
        
        # PREVIEWER
        self.preview = BrushPreviewWidget()
        layout.addWidget(self.preview)
        
        layout.addSpacing(10)

        # --- SLIDER SECTIONS ---
        self.add_section_header("BASICS", layout)
        self.add_slider("SIZE", 1, 500, self.canvas.brush_size, self.on_size_change, layout)
        
        current_flow = int(getattr(self.canvas, 'brush_flow', .99) * 100)
        self.add_slider("FLOW", 1, 100, current_flow, self.on_flow_change, layout)
        
        current_spacing = int(getattr(self.canvas, 'brush_spacing_factor', 0.1) * 100)
        self.add_slider("SPACING", 1, 50, current_spacing, self.on_spacing_change, layout)
        
        layout.addSpacing(10)
        self.add_section_header("DYNAMICS", layout)
        
        # Jitter Sliders
        val_sz = int(getattr(self.canvas, 'jitter_size', 0.0) * 100)
        self.add_slider("SIZE JITTER", 0, 100, val_sz, lambda v: self.update_jitter('size', v), layout)
        
        val_an = int(getattr(self.canvas, 'jitter_angle', 0.0) * 100)
        self.add_slider("ANGLE JITTER", 0, 100, val_an, lambda v: self.update_jitter('angle', v), layout)
        
        val_sc = int(getattr(self.canvas, 'jitter_scatter', 0.0) * 100)
        self.add_slider("SCATTER", 0, 100, val_sc, lambda v: self.update_jitter('scatter', v), layout)
        
        val_hue = int(getattr(self.canvas, 'jitter_hue', 0.0) * 100)
        self.add_slider("HUE JITTER", 0, 100, val_hue, lambda v: self.update_jitter('hue', v), layout)
        
        layout.addStretch()

    def add_section_header(self, text, layout):
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #888; font-size: 10px; font-weight: bold; margin-top: 5px; border-bottom: 1px solid #EEE; padding-bottom: 2px;")
        layout.addWidget(lbl)

    def add_slider(self, label, min_v, max_v, default, callback, layout):
        container = QWidget()
        l = QVBoxLayout(container)
        l.setContentsMargins(0,0,0,0)
        l.setSpacing(2)
        
        txt = QLabel(label)
        txt.setStyleSheet("font-size: 9px; color: #555; font-weight: 600;")
        l.addWidget(txt)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(default)
        slider.valueChanged.connect(callback)
        l.addWidget(slider)
        
        layout.addWidget(container)
        return slider

    # --- LOGIC HANDLERS ---
    def on_size_change(self, value):
        self.canvas.set_brush_size(value)
        self.refresh_preview()

    def on_spacing_change(self, value):
        self.canvas.set_brush_spacing(value / 100.0)
        self.refresh_preview()
        
    def on_flow_change(self, value):
        self.canvas.set_brush_flow(value / 100.0)
        self.refresh_preview()

    def update_jitter(self, type_name, value):
        float_val = value / 100.0
        if type_name == 'size': self.canvas.set_jitter_size(float_val)
        elif type_name == 'angle': self.canvas.set_jitter_angle(float_val)
        elif type_name == 'scatter': self.canvas.set_jitter_scatter(float_val)
        elif type_name == 'hue': self.canvas.set_jitter_hue(float_val)
        self.refresh_preview()

    def refresh_preview(self):
        spacing_px = max(1, self.canvas.brush_size * getattr(self.canvas, 'brush_spacing_factor', 0.1))
        self.preview.update_settings(
            self.canvas.brush_size, 
            self.canvas.brush_shape_name,
            self.canvas.brush_color,
            spacing_px,
            getattr(self.canvas, 'brush_flow', 1.0),
            getattr(self.canvas, 'jitter_size', 0.0),
            getattr(self.canvas, 'jitter_angle', 0.0),
            getattr(self.canvas, 'jitter_scatter', 0.0),
            getattr(self.canvas, 'jitter_hue', 0.0)
        )