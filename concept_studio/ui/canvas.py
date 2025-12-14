from PyQt6.QtWidgets import QWidget, QFileDialog
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QPointF, QObject
from PyQt6.QtGui import (QPainter, QPen, QColor, QImage, QTabletEvent, 
                        QTransform, QPainterPath, QPolygonF, QMouseEvent, QKeyEvent)

from logic.history import HistoryManager
from logic.tools.brush import BrushTool
from logic.tools.transform import TransformTool
from logic.tools.selection import LassoTool
from logic.tools.bucket import BucketTool

BLEND_MODES = {
    "Normal": QPainter.CompositionMode.CompositionMode_SourceOver,
    "Multiply": QPainter.CompositionMode.CompositionMode_Multiply,
    "Screen": QPainter.CompositionMode.CompositionMode_Screen,
    "Overlay": QPainter.CompositionMode.CompositionMode_Overlay,
    "Darken": QPainter.CompositionMode.CompositionMode_Darken,
    "Lighten": QPainter.CompositionMode.CompositionMode_Lighten,
}

class Canvas(QWidget):
    def __init__(self, parent=None, width=1920, height=1080):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # === View State === #
        self.canvas_width = width
        self.canvas_height = height
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # === Data === #
        self.layers = []
        self._init_layers()
        self.active_layer_index = 1
        self.history = HistoryManager()

        # === Input State (Shared with Tools) === #
        self.last_mouse_pos = QPoint()
        self.last_canvas_pos = QPointF()
        self.brush_color = QColor(0, 0, 0)
        self.brush_size = 5
        self.pressure = 1.0
        self.panning = False
        
        # === Shared Selection State === #
        self.selection_path = QPainterPath()
        self.lasso_points = []
        self.is_selecting = False

        # === TOOL MANAGER === #
        self.tools = {
            "brush": BrushTool(self, is_eraser=False),
            "eraser": BrushTool(self, is_eraser=True),
            "move": TransformTool(self, mode="move"),
            "rotate": TransformTool(self, mode="rotate"),
            "scale": TransformTool(self, mode="scale"),
            "lasso": LassoTool(self, poly_mode=False),
            "poly_lasso": LassoTool(self, poly_mode=True),
            "bucket": BucketTool(self)
        }
        self.current_tool = "brush" 
        
        # === Cursor State === #
        self.cursor_pos = QPointF(0, 0)
        self.show_cursor_circle = False

    def _init_layers(self):
        bg = Layer("Background", self.canvas_width, self.canvas_height)
        bg.image.fill(Qt.GlobalColor.white)
        self.layers.append(bg)
        l1 = Layer("Layer 1", self.canvas_width, self.canvas_height)
        self.layers.append(l1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("#1e1e1e"))

        view_transform = QTransform()
        view_transform.translate(self.offset_x, self.offset_y)
        view_transform.scale(self.scale_factor, self.scale_factor)
        
        painter.setTransform(view_transform)

        for i, layer in enumerate(self.layers):
            if layer.visible:
                painter.setOpacity(layer.opacity)
                mode = BLEND_MODES.get(layer.blend_mode, QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.setCompositionMode(mode)

                t = QTransform()
                t.translate(layer.x, layer.y)
                cx, cy = layer.image.width()/2, layer.image.height()/2
                t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)

                painter.setTransform(t, True) 
                painter.drawImage(0, 0, layer.image)
                painter.setTransform(view_transform)

                # === Draw Transform Bounds === #
                if self.current_tool in ["move", "rotate", "scale"] and i == self.active_layer_index:
                    mapped_rect = t.map(QPolygonF(QRectF(0, 0, layer.image.width(), layer.image.height())))
                    color = "#00aaff"
                    if self.current_tool == "rotate": color = "#ffaa00"
                    elif self.current_tool == "scale": color = "#00ff00"
                    
                    pen = QPen(QColor(color), 2 if not layer.is_floating else 3)
                    pen.setStyle(Qt.PenStyle.SolidLine if layer.is_floating else Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPolygon(mapped_rect)

        if not self.selection_path.isEmpty():
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawPath(self.selection_path)
            
        if self.current_tool in ["lasso", "poly_lasso"] and self.lasso_points:
            pen = QPen(Qt.GlobalColor.yellow, 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawPolyline(QPolygonF([QPointF(p) for p in self.lasso_points]))

        # === Cursor Ghost === #
        if self.show_cursor_circle and self.current_tool in ["brush", "eraser"]:
            painter.setTransform(view_transform)
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            radius = self.brush_size / 2
            painter.setPen(QPen(QColor(0,0,0,150), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self.cursor_pos, radius, radius)
            painter.setPen(QPen(QColor(255,255,255,150), 1))
            painter.drawEllipse(self.cursor_pos, radius-1, radius-1)

    # === DELEGATED INPUT EVENTS === #
    def mousePressEvent(self, event):
        self.setFocus()
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.panning = True; self.last_mouse_pos = event.pos(); return

        canvas_pos = self.map_to_canvas(event.pos())
        self.last_mouse_pos = event.pos()

        # === Delegate Tool Events === #
        if self.current_tool in self.tools:
            self.tools[self.current_tool].mouse_press(event, canvas_pos)

    def mouseMoveEvent(self, event):
        canvas_pos = self.map_to_canvas(event.pos())
        self.cursor_pos = canvas_pos
        self.show_cursor_circle = True
        self.update() # For cursor ghost

        if self.panning:
            delta = event.pos() - self.last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.update()
            return

        if self.current_tool in self.tools:
            self.tools[self.current_tool].mouse_move(event, canvas_pos)

    def mouseReleaseEvent(self, event):
        if self.panning: self.panning = False; return
        if self.current_tool in self.tools:
            self.tools[self.current_tool].mouse_release(event, None)
        self.update()

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()

        # === Global Undo/Redo === #
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Z:
                self.history.undo(self.layers); self.update(); return
            elif key == Qt.Key.Key_Y:
                self.history.redo(self.layers); self.update(); return

        # === Delegate Tool Keys (Enter, etc.) === #
        if self.current_tool in self.tools:
            self.tools[self.current_tool].key_press(event)
            
        self.handle_shortcuts(key)

    def map_to_canvas(self, widget_point):
        x = (widget_point.x() - self.offset_x) / self.scale_factor
        y = (widget_point.y() - self.offset_y) / self.scale_factor
        return QPointF(x, y)

    def handle_shortcuts(self, key):
        if not hasattr(self.parent(), 'station'): return
        station = self.parent().station
        if key == Qt.Key.Key_B: station.set_tool("brush")
        elif key == Qt.Key.Key_E: station.set_tool("eraser")
        elif key == Qt.Key.Key_V: station.set_tool("move")
        elif key == Qt.Key.Key_R: station.set_tool("rotate")
        elif key == Qt.Key.Key_L: station.set_tool("lasso")
        elif key == Qt.Key.Key_P: station.set_tool("poly_lasso")
        elif key == Qt.Key.Key_G: station.set_tool("bucket")
        elif key == Qt.Key.Key_BracketLeft: 
            self.brush_size = max(1, self.brush_size - 5)
            station.slider_size.setValue(self.brush_size)
            self.update()
        elif key == Qt.Key.Key_BracketRight: 
            self.brush_size = min(100, self.brush_size + 5)
            station.slider_size.setValue(self.brush_size)
            self.update()

    def enterEvent(self, event):
        # === Reset cursor on entry === #
        if self.current_tool == "brush": self.setCursor(Qt.CursorShape.BlankCursor)
        else: self.setCursor(Qt.CursorShape.ArrowCursor)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.show_cursor_circle = False
        self.update()
        super().leaveEvent(event)

    def lift_selection_to_layer(self):
        if not (0 <= self.active_layer_index < len(self.layers)): return False
        source_layer = self.layers[self.active_layer_index]
        if not self.selection_path.isEmpty():
            crop_rect = self.selection_path.boundingRect().toRect()
        else: return False 
        if crop_rect.isEmpty(): return False

        self.history.save_state(self.active_layer_index, source_layer.image)
        floating_layer = Layer("Float Object", crop_rect.width(), crop_rect.height())
        floating_layer.is_floating = True
        
        painter = QPainter(floating_layer.image)
        painter.drawImage(0, 0, source_layer.image, crop_rect.x(), crop_rect.y(), crop_rect.width(), crop_rect.height())
        painter.end()
        
        eraser = QPainter(source_layer.image)
        eraser.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        eraser.setClipPath(self.selection_path)
        eraser.fillRect(source_layer.image.rect(), Qt.GlobalColor.white)
        eraser.end()
        
        floating_layer.x = crop_rect.x()
        floating_layer.y = crop_rect.y()
        self.layers.append(floating_layer)
        self.active_layer_index = len(self.layers) - 1
        self.selection_path = QPainterPath()
        self.update()
        return True

    def commit_transform(self):
        if not (0 <= self.active_layer_index < len(self.layers)): return
        layer = self.layers[self.active_layer_index]
        
        if not layer.is_floating:
            # === Normal Layer Bake === #
            if layer.x == 0 and layer.y == 0 and layer.rotation == 0 and layer.scale_x == 1: return
            self.history.save_state(self.active_layer_index, layer.image)
            new_image = QImage(self.canvas_width, self.canvas_height, QImage.Format.Format_ARGB32_Premultiplied)
            new_image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(new_image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            t = QTransform()
            t.translate(layer.x, layer.y)
            cx, cy = layer.image.width()/2, layer.image.height()/2
            t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)
            painter.setTransform(t)
            painter.drawImage(0, 0, layer.image)
            painter.end()
            layer.image = new_image
            layer.x=0; layer.y=0; layer.rotation=0; layer.scale_x=1; layer.scale_y=1
            self.update()
        else:
            # === Float Merge Down === #
            target_idx = self.active_layer_index - 1
            if target_idx < 0: return
            target_layer = self.layers[target_idx]
            self.history.save_state(target_idx, target_layer.image)
            painter = QPainter(target_layer.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            t = QTransform()
            t.translate(layer.x, layer.y)
            cx, cy = layer.image.width()/2, layer.image.height()/2
            t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)
            painter.setTransform(t)
            painter.drawImage(0, 0, layer.image)
            painter.end()
            del self.layers[self.active_layer_index]
            self.active_layer_index = target_idx
            self.update()

    # === IMPORTANT: Keep the Layer class definition at the bottom! === #

    def import_image_layer(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Import Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not filename: return
        imported_img = QImage(filename)
        if imported_img.isNull(): return
        self.add_layer()
        current_layer = self.layers[self.active_layer_index]
        current_layer.name = f"Import: {filename.split('/')[-1]}"
        self.history.save_state(self.active_layer_index, current_layer.image)
        painter = QPainter(current_layer.image)
        painter.drawImage(0, 0, imported_img)
        painter.end()
        self.update()

    def delete_active_layer(self):
        if len(self.layers) <= 1: return False
        del self.layers[self.active_layer_index]
        if self.active_layer_index >= len(self.layers): self.active_layer_index = len(self.layers) - 1
        self.history.undo_stack.clear()
        self.update()
        return True

    def add_layer(self):
        new_layer = Layer(f"Layer {len(self.layers)}", self.canvas_width, self.canvas_height)
        self.layers.append(new_layer)
        self.active_layer_index = len(self.layers) - 1
        self.update()

    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0
        self.scale_factor *= 1.1 if zoom_in else 0.9
        self.scale_factor = max(0.1, min(self.scale_factor, 5.0))
        self.update()

    def tabletEvent(self, event):
        self.pressure = event.pressure()
        pass 

class Layer:
    def __init__(self, name, width, height):
        self.name = name
        self.visible = True
        self.opacity = 1.0
        self.blend_mode = "Normal"
        self.is_floating = False
        self.x=0.0; self.y=0.0; self.scale_x=1.0; self.scale_y=1.0; self.rotation=0.0
        self.image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(Qt.GlobalColor.transparent)