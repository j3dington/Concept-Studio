from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor, QTransform
from .base import BaseTool

class BrushTool(BaseTool):
    def __init__(self, canvas, is_eraser=False):
        super().__init__(canvas)
        self.is_eraser = is_eraser

    def mouse_press(self, event, pos):
        # === Save History === #
        if 0 <= self.canvas.active_layer_index < len(self.canvas.layers):
            layer = self.canvas.layers[self.canvas.active_layer_index]
            self.canvas.history.save_state(self.canvas.active_layer_index, layer.image)
        
        self.canvas.last_canvas_pos = pos
        self.canvas.pressure = 1.0 # (Or get pressure from event if available)
        
        self.draw_stroke(pos)

    def mouse_move(self, event, pos):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.draw_stroke(pos)

    def draw_stroke(self, current_point):
        if not (0 <= self.canvas.active_layer_index < len(self.canvas.layers)): return
        layer = self.canvas.layers[self.canvas.active_layer_index]
        if not layer.visible: return

        # === Matrix Logic === #
        t = QTransform()
        t.translate(layer.x, layer.y)
        cx, cy = layer.image.width()/2, layer.image.height()/2
        t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)
        
        inv, _ = t.inverted()
        local_start = inv.map(self.canvas.last_canvas_pos)
        local_end = inv.map(current_point)
        
        painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # === Clipping === #
        if not self.canvas.selection_path.isEmpty():
            mapped_path = self.canvas.selection_path.transformed(inv)
            painter.setClipPath(mapped_path)
            
        size = self.canvas.brush_size # pressure support can be added here
        color = QColor(self.canvas.brush_color)
        
        if self.is_eraser:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        else:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        painter.setPen(QPen(color, size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(local_start, local_end)
        
        self.canvas.last_canvas_pos = current_point
        self.canvas.update()