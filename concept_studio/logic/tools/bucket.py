from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, qRed, qGreen, qBlue, qAlpha
from .base import BaseTool

class BucketTool(BaseTool):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.tolerance = 32 
        self.contiguous = True 

    def mouse_press(self, event, pos):
        if not (0 <= self.canvas.active_layer_index < len(self.canvas.layers)): return
        layer = self.canvas.layers[self.canvas.active_layer_index]
        if not layer.visible: return

        # === Save history before the expensive operation === #
        self.canvas.history.save_state(self.canvas.active_layer_index, layer.image)
        
        # === We pass the raw integer color value for speed === #
        self.flood_fill(pos.toPoint(), layer)

    def colors_match(self, color1_int, color2_int):
        """
        Compare two colors with tolerance.
        """
        # === Exact Match Shortcut === #
        if self.tolerance == 0:
            return color1_int == color2_int

        # === Extract RGB Components === #
        r1, g1, b1 = qRed(color1_int), qGreen(color1_int), qBlue(color1_int)
        r2, g2, b2 = qRed(color2_int), qGreen(color2_int), qBlue(color2_int)

        # === Calculate simple difference === #
        diff = abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
        
        # === Threshold: Tolerance * 3 === #
        return diff <= (self.tolerance * 3)

    def flood_fill(self, start_point, layer):
        w, h = layer.image.width(), layer.image.height()
        x, y = start_point.x(), start_point.y()
        
        if not (0 <= x < w and 0 <= y < h): return

        # === Get Colors as Raw Integers (ARGB32) === #
        target_int = layer.image.pixel(x, y)
        
        # === Convert brush color to QColor then to ARGB integer === #
        brush_qcolor = QColor(self.canvas.brush_color)
        fill_int = brush_qcolor.rgba() # Returns integer
        
        # === Optimize: If target color is same as fill color, no need to proceed === #
        if target_int == fill_int: return

        print(f"🪣 Flood Fill: Tolerance {self.tolerance}")

        # === Prepare Painter === #
        painter = QPainter(layer.image)
        painter.setPen(QPen(brush_qcolor))
        
        # === The Algorithm (Scanline with Tolerance) === #
        stack = [(x, y)]
        visited = set() # Set of tuples (x, y)
        
        # === Initial check to ensure we actually match the start node === #
        if not self.colors_match(target_int, target_int): return 

        while stack:
            cx, cy = stack.pop()
            
            if (cx, cy) in visited: continue
            
            # === Bounds Check === #
            if not (0 <= cx < w and 0 <= cy < h): continue
            
            # === Color Match Check (The "Fuzzy" Logic) ===
            current_pixel_int = layer.image.pixel(cx, cy)
            if not self.colors_match(current_pixel_int, target_int): 
                continue
            
            # === SCANLINE OPTIMIZATION ===
            left_x = cx
            while left_x > 0:
                left_pixel = layer.image.pixel(left_x - 1, cy)
                if self.colors_match(left_pixel, target_int):
                    left_x -= 1
                else:
                    break
            
            right_x = cx
            while right_x < w - 1:
                right_pixel = layer.image.pixel(right_x + 1, cy)
                if self.colors_match(right_pixel, target_int):
                    right_x += 1
                else:
                    break
            
            # === Fill the row === #
            painter.drawLine(left_x, cy, right_x, cy)
            
            # === Add neighbors to stack (Check rows above and below) === #
            for i in range(left_x, right_x + 1):
                visited.add((i, cy))
                
                # === Check Up === #
                if cy > 0:
                    up_pixel = layer.image.pixel(i, cy - 1)
                    if self.colors_match(up_pixel, target_int) and (i, cy - 1) not in visited:
                        stack.append((i, cy - 1))
                        
                # === Check Down === #
                if cy < h - 1:
                    down_pixel = layer.image.pixel(i, cy + 1)
                    if self.colors_match(down_pixel, target_int) and (i, cy + 1) not in visited:
                        stack.append((i, cy + 1))
                    
        painter.end()
        self.canvas.update()
        print("✅ Fill Complete")