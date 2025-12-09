from PyQt6.QtWidgets import QWidget, QFileDialog
from PyQt6.QtCore import Qt, QPoint, QRect, QRectF, QPointF
from PyQt6.QtGui import (QPainter, QPen, QColor, QImage, QTabletEvent, 
                         QTransform, QPainterPath, QPolygonF)

# Import dependencies (Adjust based on your exact file names if needed)
from logic.history import HistoryManager
# We need Layer definition. If it's in this file, great. If not, import it.
# For this code block, I will include the updated Layer class at the bottom.

BLEND_MODES = {
    "Normal": QPainter.CompositionMode.CompositionMode_SourceOver,
    "Multiply": QPainter.CompositionMode.CompositionMode_Multiply,
    "Screen": QPainter.CompositionMode.CompositionMode_Screen,
    "Overlay": QPainter.CompositionMode.CompositionMode_Overlay,
    "Darken": QPainter.CompositionMode.CompositionMode_Darken,
    "Lighten": QPainter.CompositionMode.CompositionMode_Lighten,
}

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # View State
        self.canvas_width = 1920
        self.canvas_height = 1080
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0

        # Data
        self.layers = []
        self._init_layers()
        self.active_layer_index = 1
        self.history = HistoryManager()

        # Tools & Input
        self.current_tool = "brush" 
        self.drawing = False
        self.panning = False
        self.last_mouse_pos = QPoint()
        self.last_canvas_pos = QPointF()
        
        # Brush
        self.brush_color = QColor(0, 0, 0)
        self.brush_size = 5
        self.pressure = 1.0
        self.is_eraser = False

        # Selection & Transform State
        self.selection_path = QPainterPath()
        self.lasso_points = []
        self.is_selecting = False
        self.transform_start_pos = QPoint()
        
        # Cursor State
        self.cursor_pos = QPointF(0, 0)
        self.show_cursor_circle = False

    def _init_layers(self):
        bg = Layer("Background", self.canvas_width, self.canvas_height)
        bg.image.fill(Qt.GlobalColor.white)
        self.layers.append(bg)
        l1 = Layer("Layer 1", self.canvas_width, self.canvas_height)
        self.layers.append(l1)

    # --- CORE LOGIC: LIFT & STAMP ---
    
    def lift_selection_to_layer(self):
        """Cuts selected pixels into a floating layer for transformation."""
        if not (0 <= self.active_layer_index < len(self.layers)): return False
        source_layer = self.layers[self.active_layer_index]
        
        # 1. Determine Crop Area
        if not self.selection_path.isEmpty():
            crop_rect = self.selection_path.boundingRect().toRect()
        else:
            # If no selection, we don't auto-lift whole layer in this version
            # (Users expect to select something first)
            return False 
            
        if crop_rect.isEmpty(): return False

        print("🚀 Lifting pixels to Floating Layer...")
        
        # 2. Save History BEFORE cutting
        self.history.save_state(self.active_layer_index, source_layer.image)

        # 3. Create Float Layer
        floating_layer = Layer("Float Object", crop_rect.width(), crop_rect.height())
        floating_layer.is_floating = True
        
        # 4. Copy Pixels (Source -> Float)
        painter = QPainter(floating_layer.image)
        # Draw from source_layer, grabbing only the crop_rect area
        painter.drawImage(0, 0, source_layer.image, crop_rect.x(), crop_rect.y(), crop_rect.width(), crop_rect.height())
        painter.end()
        
        # 5. Cut Pixels (Erase from Source)
        eraser = QPainter(source_layer.image)
        eraser.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        eraser.setClipPath(self.selection_path)
        eraser.fillRect(source_layer.image.rect(), Qt.GlobalColor.white) # Color ignored in Clear mode
        eraser.end()
        
        # 6. Position Float Layer
        floating_layer.x = crop_rect.x()
        floating_layer.y = crop_rect.y()
        
        # 7. Add to Stack
        self.layers.append(floating_layer)
        self.active_layer_index = len(self.layers) - 1
        
        # Clear selection (it's now defined by the layer bounds)
        self.selection_path = QPainterPath()
        self.update()
        return True

    def commit_transform(self):
        """Stamps the floating layer back down."""
        if not (0 <= self.active_layer_index < len(self.layers)): return
        layer = self.layers[self.active_layer_index]
        
        # CASE 1: Normal Layer (Just bake transform)
        if not layer.is_floating:
            if layer.x == 0 and layer.y == 0 and layer.rotation == 0 and layer.scale_x == 1: return
            # ... (Standard bake logic we wrote before) ...
            # I'll include the short version here:
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

        # CASE 2: Floating Object (Merge Down)
        else:
            print("🔨 Merging Floating Object Down...")
            # Target is the layer below
            target_idx = self.active_layer_index - 1
            if target_idx < 0: return # Should not happen
            
            target_layer = self.layers[target_idx]
            self.history.save_state(target_idx, target_layer.image)
            
            painter = QPainter(target_layer.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Recreate Float Matrix
            t = QTransform()
            t.translate(layer.x, layer.y)
            cx, cy = layer.image.width()/2, layer.image.height()/2
            t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)
            
            painter.setTransform(t)
            painter.drawImage(0, 0, layer.image)
            painter.end()
            
            # Remove float layer
            del self.layers[self.active_layer_index]
            self.active_layer_index = target_idx
            
            self.update()

    # --- RENDER LOOP ---
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

                # Matrix Math
                t = QTransform()
                t.translate(layer.x, layer.y)
                cx, cy = layer.image.width()/2, layer.image.height()/2
                t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)

                # Draw Layer
                # Note: We multiply matrices (View * Layer) implicitly by setting transform repeatedly? 
                # Better way: Save/Restore or reset view transform.
                # Let's reset to view transform first:
                painter.setTransform(t, True) # Combine with View
                painter.drawImage(0, 0, layer.image)
                painter.setTransform(view_transform) # Reset for next layer

                # Draw Bounds (Only for active transform)
                if self.current_tool in ["move", "rotate", "scale"] and i == self.active_layer_index:
                    mapped_rect = t.map(QPolygonF(QRectF(0, 0, layer.image.width(), layer.image.height())))
                    
                    color = "#00aaff"
                    if self.current_tool == "rotate": color = "#ffaa00"
                    elif self.current_tool == "scale": color = "#00ff00"
                    
                    pen = QPen(QColor(color), 2 if not layer.is_floating else 3) # Thicker if floating
                    pen.setStyle(Qt.PenStyle.SolidLine if layer.is_floating else Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPolygon(mapped_rect)
                    
                    # Pivot Point
                    if self.current_tool == "rotate":
                        pivot = t.map(QPointF(cx, cy))
                        painter.setBrush(Qt.GlobalColor.white)
                        painter.setPen(Qt.GlobalColor.black)
                        painter.drawEllipse(pivot, 4, 4)

        # Draw Selection
        if not self.selection_path.isEmpty():
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.selection_path)
            
        # Draw Lasso Line
        if self.current_tool in ["lasso", "poly_lasso"] and self.lasso_points:
            pen = QPen(Qt.GlobalColor.yellow, 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawPolyline(QPolygonF([QPointF(p) for p in self.lasso_points]))

        # Draw Cursor Ghost
        if self.show_cursor_circle and self.current_tool in ["brush", "eraser"]:
            painter.setTransform(view_transform) # Ensure scaling is correct
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            radius = self.brush_size / 2
            painter.setPen(QPen(QColor(0,0,0,150), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self.cursor_pos, radius, radius)
            painter.setPen(QPen(QColor(255,255,255,150), 1))
            painter.drawEllipse(self.cursor_pos, radius-1, radius-1)

    # --- INPUT EVENTS ---
    def mousePressEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier or event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        canvas_pos = self.map_to_canvas(event.pos())
        self.last_mouse_pos = event.pos()

        # TRANSFORM START
        if self.current_tool in ["move", "rotate", "scale"]:
            # CHECK LIFT: If we have a selection and layer isn't floating yet...
            active_layer = self.layers[self.active_layer_index]
            if not self.selection_path.isEmpty() and not active_layer.is_floating:
                if self.lift_selection_to_layer():
                    # If lift succeeded, we are now transforming the NEW float layer
                    pass 
            
            self.drawing = True
            self.transform_start_pos = event.pos()

        elif self.current_tool == "lasso":
            self.is_selecting = True
            self.selection_path = QPainterPath()
            self.lasso_points = [canvas_pos]

        elif self.current_tool == "poly_lasso":
            if not self.lasso_points: self.selection_path = QPainterPath()
            self.lasso_points.append(canvas_pos)
            self.update()

        elif self.current_tool in ["brush", "eraser"]:
            self.drawing = True
            if 0 <= self.active_layer_index < len(self.layers):
                self.history.save_state(self.active_layer_index, self.layers[self.active_layer_index].image)
            self.last_canvas_pos = canvas_pos
            self.pressure = 1.0

    def mouseMoveEvent(self, event):
        canvas_pos = self.map_to_canvas(event.pos())
        self.cursor_pos = canvas_pos
        self.show_cursor_circle = True

        if self.panning:
            delta = event.pos() - self.last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.update()

        elif self.drawing and self.current_tool in ["move", "rotate", "scale"]:
            delta = event.pos() - self.transform_start_pos
            layer = self.layers[self.active_layer_index]
            
            if self.current_tool == "rotate":
                layer.rotation += delta.x() * 0.5
            elif self.current_tool == "scale":
                change = delta.x() * 0.01
                layer.scale_x += change; layer.scale_y += change
            else: # Move
                layer.x += delta.x() / self.scale_factor
                layer.y += delta.y() / self.scale_factor
            
            self.transform_start_pos = event.pos()
            self.update()

        elif self.current_tool == "lasso" and self.is_selecting:
            self.lasso_points.append(canvas_pos)
            self.update()

        elif self.drawing and self.current_tool in ["brush", "eraser"]:
            self.draw_stroke(canvas_pos)
            
        self.update() # Constant update for cursor ghost

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.setCursor(Qt.CursorShape.CrossCursor)
        if self.current_tool == "lasso":
            self.is_selecting = False
            if len(self.lasso_points) > 2:
                self.selection_path.addPolygon(QPolygonF([QPointF(p) for p in self.lasso_points]))
                self.selection_path.closeSubpath()
            self.lasso_points = []
            self.update()
        self.drawing = False

    def leaveEvent(self, event):
        self.show_cursor_circle = False
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        key = event.key()
        
        # Confirm Poly Lasso
        if self.current_tool == "poly_lasso" and key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
             if len(self.lasso_points) > 2:
                self.selection_path.addPolygon(QPolygonF([QPointF(p) for p in self.lasso_points]))
                self.selection_path.closeSubpath()
             self.lasso_points = []
             self.update()

        # Commit Transform
        if self.current_tool in ["move", "rotate", "scale"] and key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.commit_transform()
            # Switch back to brush
            if hasattr(self.parent(), 'station'): self.parent().station.set_tool("brush")

        # Shortcuts Handler
        self.handle_shortcuts(key)
        
        # Propagate to parent (Main Window) for global keys if needed
        super().keyPressEvent(event)

    def handle_shortcuts(self, key):
        # Access sibling components via Parent (Duck Typing)
        if not hasattr(self.parent(), 'station'): return
        
        station = self.parent().station
        if key == Qt.Key.Key_B: station.set_tool("brush")
        elif key == Qt.Key.Key_E: station.set_tool("eraser")
        elif key == Qt.Key.Key_V: station.set_tool("move")
        elif key == Qt.Key.Key_R: station.set_tool("rotate")
        elif key == Qt.Key.Key_L: station.set_tool("lasso")
        elif key == Qt.Key.Key_P: station.set_tool("poly_lasso")
        elif key == Qt.Key.Key_BracketLeft: 
            self.brush_size = max(1, self.brush_size - 5)
            station.slider_size.setValue(self.brush_size)
        elif key == Qt.Key.Key_BracketRight: 
            self.brush_size = min(100, self.brush_size + 5)
            station.slider_size.setValue(self.brush_size)

    # ... (Keep existing methods: map_to_canvas, import_image_layer, draw_stroke, delete_active_layer, add_layer, tabletEvent, wheelEvent) ...
    # Make sure to keep the Layer class definition below if it's not imported!

    def map_to_canvas(self, widget_point):
        x = (widget_point.x() - self.offset_x) / self.scale_factor
        y = (widget_point.y() - self.offset_y) / self.scale_factor
        return QPointF(x, y)

    def draw_stroke(self, current_point):
        if not (0 <= self.active_layer_index < len(self.layers)): return
        layer = self.layers[self.active_layer_index]
        if not layer.visible: return
        
        # Matrix Inversion for Drawing on Rotated Layers
        t = QTransform()
        t.translate(layer.x, layer.y)
        cx, cy = layer.image.width()/2, layer.image.height()/2
        t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)
        
        inv, _ = t.inverted()
        local_start = inv.map(self.last_canvas_pos)
        local_end = inv.map(current_point)
        
        painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.selection_path.isEmpty():
            mapped_path = self.selection_path.transformed(inv)
            painter.setClipPath(mapped_path)
            
        size = self.brush_size * self.pressure
        color = QColor(self.brush_color)
        if self.is_eraser: painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        else: painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        painter.setPen(QPen(color, size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(local_start, local_end)
        self.last_canvas_pos = current_point
        self.update()

    def add_layer(self):
        new_layer = Layer(f"Layer {len(self.layers)}", self.canvas_width, self.canvas_height)
        self.layers.append(new_layer)
        self.active_layer_index = len(self.layers) - 1
        self.update()

    def delete_active_layer(self):
        if len(self.layers) <= 1: return False
        del self.layers[self.active_layer_index]
        if self.active_layer_index >= len(self.layers): self.active_layer_index = len(self.layers) - 1
        self.history.undo_stack.clear()
        self.update()
        return True

    def tabletEvent(self, event):
        self.pressure = event.pressure()
        widget_pos = QPoint(int(event.position().x()), int(event.position().y()))
        if event.type() == QTabletEvent.Type.TabletPress:
            self.drawing = True
            if 0 <= self.active_layer_index < len(self.layers):
                self.history.save_state(self.active_layer_index, self.layers[self.active_layer_index].image)
            self.last_canvas_pos = self.map_to_canvas(widget_pos)
        elif event.type() == QTabletEvent.Type.TabletMove:
            if self.drawing: self.draw_stroke(self.map_to_canvas(widget_pos))
        elif event.type() == QTabletEvent.Type.TabletRelease:
            self.drawing = False

    def wheelEvent(self, event):
        zoom_in = event.angleDelta().y() > 0
        self.scale_factor *= 1.1 if zoom_in else 0.9
        self.scale_factor = max(0.1, min(self.scale_factor, 5.0))
        self.update()

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

class Layer:
    def __init__(self, name, width, height):
        self.name = name
        self.visible = True
        self.opacity = 1.0
        self.blend_mode = "Normal"
        self.is_floating = False # New Flag
        self.x=0.0; self.y=0.0; self.scale_x=1.0; self.scale_y=1.0; self.rotation=0.0
        self.image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(Qt.GlobalColor.transparent)
