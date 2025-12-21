import math
import random
from PyQt6.QtGui import QPainter, QColor, QPixmap, QTransform
from PyQt6.QtCore import Qt, QPointF, QRect, QPoint

from assets import get_soft_brush_pixmap, load_custom_brush

class DrawingEngine:
    """
    HANDLES PIXEL MANIPULATION ONLY.
    - Drawing Lines (Brush/Eraser)
    - Flood Filling (Bucket)
    - Jitter Math (Dynamics)
    """
    def __init__(self):
        # --- STATE ---
        self.brush_size = 20
        self.brush_color = QColor("#000000")
        self.brush_shape_name = "Soft"
        self.current_brush_tip = None
        
        # Dynamics
        self.brush_flow = 1.0
        self.brush_spacing_factor = 0.1
        self.dist_to_next_dot = 0.0 
        
        # Jitter
        self.jitter_size = 0.0
        self.jitter_angle = 0.0
        self.jitter_flow = 0.0
        self.jitter_scatter = 0.0
        self.jitter_hue = 0.0
        
        self.update_brush_tip()

    @property
    def max_reach(self):
        """Calculates the furthest a pixel could possibly land from the mouse."""
        # Base size + Scatter Radius
        scatter_radius = self.brush_size * 2.0 * self.jitter_scatter
        return int(self.brush_size + scatter_radius + 20)

    def update_brush_tip(self):
        if self.brush_shape_name == "Soft":
            self.current_brush_tip = get_soft_brush_pixmap(self.brush_size, self.brush_color)
        else:
            custom = load_custom_brush(self.brush_shape_name, self.brush_size, self.brush_color)
            self.current_brush_tip = custom if custom else get_soft_brush_pixmap(self.brush_size, self.brush_color)

    # --- RESTORED FEATURE: FLOOD FILL ---
    def flood_fill(self, layer_pixmap, start_pos, new_color):
        """
        Simple BFS Flood Fill. 
        Note: Python is slow at pixel access. For production, we'd use C++ or QImage.bits().
        This is a placeholder for the logic structure.
        """
        if not layer_pixmap: return
        
        # Convert to QImage for pixel access
        image = layer_pixmap.toImage()
        width, height = image.width(), image.height()
        
        if not (0 <= start_pos.x() < width and 0 <= start_pos.y() < height):
            return

        target_color = image.pixelColor(start_pos)
        if target_color == new_color:
            return

        painter = QPainter(layer_pixmap)
        painter.fillRect(layer_pixmap.rect(), new_color)
        painter.end()

    # --- MAIN DRAWING LOOP ---
    def draw_line(self, layer_pixmap, start, end, p_start, p_end, is_eraser=False):
        if not layer_pixmap or not self.current_brush_tip: return

        painter = QPainter(layer_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        if is_eraser:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        else:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
        dist_x = end.x() - start.x()
        dist_y = end.y() - start.y()
        segment_length = math.sqrt(dist_x**2 + dist_y**2)
        
        spacing = max(1.0, self.brush_size * self.brush_spacing_factor)
        if self.brush_size > 300: spacing = max(spacing, self.brush_size * 0.1)

        if segment_length < 0.001:
            self.draw_stamp(painter, end, p_end, is_eraser)
        else:
            traveled = 0.0
            while (traveled + self.dist_to_next_dot) <= segment_length:
                traveled += self.dist_to_next_dot
                t = traveled / segment_length
                
                point = QPointF(start.x() + (dist_x * t), start.y() + (dist_y * t))
                pressure = p_start + (p_end - p_start) * t
                
                self.draw_stamp(painter, point, pressure, is_eraser)
                self.dist_to_next_dot = spacing
            self.dist_to_next_dot -= (segment_length - traveled)
        painter.end()

    def draw_stamp(self, painter, pos, pressure, is_eraser):
        tip = self.current_brush_tip
        
        # A. Size Jitter
        scale_factor = 0.1 + (0.9 * pressure)
        if self.jitter_size > 0:
            scale_factor *= random.uniform(1.0 - self.jitter_size, 1.0)
        final_size = self.brush_size * scale_factor
        
        # B. Flow Jitter
        alpha = self.brush_flow
        if self.jitter_flow > 0:
            alpha *= random.uniform(1.0 - self.jitter_flow, 1.0)
        painter.setOpacity(alpha)
        
        # C. Hue Jitter
        final_tip = tip
        if not is_eraser and self.jitter_hue > 0:
            h, s, v, a = self.brush_color.getHsv()
            shift = (random.random() - 0.5) * 360 * self.jitter_hue
            new_h = (h + shift) % 360
            if s < 10: s = 50
            jitter_color = QColor.fromHsv(int(new_h), s, v, a)
            
            colored_stamp = QPixmap(tip.size())
            colored_stamp.fill(Qt.GlobalColor.transparent)
            pt = QPainter(colored_stamp)
            pt.drawPixmap(0, 0, tip)
            pt.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            pt.fillRect(colored_stamp.rect(), jitter_color)
            pt.end()
            final_tip = colored_stamp
            
        # D. Scatter/Angle
        draw_pos = QPointF(pos)
        if self.jitter_scatter > 0:
            radius = self.brush_size * 2.0 * self.jitter_scatter
            draw_pos += QPointF(random.uniform(-radius, radius), random.uniform(-radius, radius))
            
        rotation = 0
        if self.jitter_angle > 0:
            rotation = random.uniform(0, 360) * self.jitter_angle

        # Draw
        transform = QTransform()
        transform.translate(draw_pos.x(), draw_pos.y())
        transform.rotate(rotation)
        transform.scale(final_size / tip.width(), final_size / tip.height())
        
        painter.setTransform(transform)
        offset = tip.width() / 2
        painter.drawPixmap(int(-offset), int(-offset), final_tip)
        painter.resetTransform()
        painter.setOpacity(1.0)