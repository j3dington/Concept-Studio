import math
import random
from collections import deque
from PyQt6.QtGui import QPainter, QColor, QPixmap, QTransform, QPainterPath, QPolygon, QPolygonF
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

    # --- ✅ FIXED: PROPER FLOOD FILL ALGORITHM ---
    def flood_fill(self, layer_pixmap, start_pos, new_color):
        """
        BFS (Breadth-First Search) flood fill algorithm.
        Fills all connected pixels of the same color starting from start_pos.
        """
        if not layer_pixmap:
            return
        
        # Convert to QImage for pixel access
        image = layer_pixmap.toImage()
        width, height = image.width(), image.height()
        
        x, y = int(start_pos.x()), int(start_pos.y())
        
        # Bounds check
        if not (0 <= x < width and 0 <= y < height):
            return

        target_color = image.pixelColor(x, y)
        
        # If already the target color, nothing to do
        if target_color == new_color:
            return

        # BFS queue - stores (x, y) positions to check
        queue = deque([(x, y)])
        visited = set()
        
        while queue:
            px, py = queue.popleft()
            
            # Skip if already visited
            if (px, py) in visited:
                continue
                
            # Skip if out of bounds
            if not (0 <= px < width and 0 <= py < height):
                continue
            
            # Check if this pixel matches the target color
            if image.pixelColor(px, py) != target_color:
                continue
            
            # Fill this pixel
            visited.add((px, py))
            image.setPixelColor(px, py, new_color)
            
            # Add 4 neighbors to queue (up, down, left, right)
            queue.append((px + 1, py))
            queue.append((px - 1, py))
            queue.append((px, py + 1))
            queue.append((px, py - 1))
        
        # Convert image back to pixmap
        painter = QPainter(layer_pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(0, 0, image)
        painter.end()

    # --- MAIN DRAWING LOOP ---
    def draw_line(self, layer_pixmap, start, end, p_start, p_end, is_eraser=False, selection_data=None):
        print("ENGINE: DRAWING AT", end)
        if not layer_pixmap or not self.current_brush_tip: 
            return

        painter = QPainter(layer_pixmap)
        
        can_clip = False
        
        if selection_data:
            rect = selection_data.get('rect')
            if rect and not rect.isEmpty():
                painter.setClipRect(rect)
                can_clip = True
                
            # 2. LASSO CHECK
            elif selection_data.get('lasso') and len(selection_data['lasso']) > 2:
                path = QPainterPath()
                points_as_floats = [QPointF(p) for p in selection_data['lasso']]
                from PyQt6.QtGui import QPolygonF 
                path.addPolygon(QPolygonF(points_as_floats))
                
                painter.setClipPath(path)
                can_clip = True
        
        if not can_clip:
            painter.setClipping(False)
        # ---------------------------
            
        # --- DRAWING MATH ---
        dist_x = end.x() - start.x()
        dist_y = end.y() - start.y()
        segment_length = math.sqrt(dist_x**2 + dist_y**2)
        spacing = max(1.0, self.brush_size * self.brush_spacing_factor)

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

        # VERY IMPORTANT: Always end the painter to "Save" changes to the RAM
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
            if s < 10: 
                s = 50
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