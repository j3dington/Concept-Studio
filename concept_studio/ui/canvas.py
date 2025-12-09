from PyQt6.QtWidgets import QWidget, QFileDialog
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QSize
from PyQt6.QtGui import (QPainter, QPen, QColor, QImage, QTabletEvent, 
                        QTransform, QPainterPath, QPolygonF)
from config import BLEND_MODES
from logic import Layer, HistoryManager


class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # View
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
        
        # Track cursor for the ghost circle
        self.cursor_pos = QPointF(0, 0)
        self.show_cursor_circle = False
        
        # Selection & Transform State
        self.selection_path = QPainterPath()
        self.lasso_points = []
        self.is_selecting = False
        self.transform_start_pos = QPoint()
        
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
        
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.scale_factor, self.scale_factor)
        
        for i, layer in enumerate(self.layers):
            if layer.visible:
                painter.setOpacity(layer.opacity)
                mode = BLEND_MODES.get(layer.blend_mode, QPainter.CompositionMode.CompositionMode_SourceOver)
                painter.setCompositionMode(mode)
                
                # --- 1. BUILD MATRIX ---
                transform = QTransform()
                transform.translate(layer.x, layer.y)
                # Rotate around center
                center_x = layer.image.width() / 2
                center_y = layer.image.height() / 2
                transform.translate(center_x, center_y)
                transform.rotate(layer.rotation)
                transform.scale(layer.scale_x, layer.scale_y)
                transform.translate(-center_x, -center_y)
                
                # --- 2. DRAW WITH MATRIX ---
                painter.setTransform(transform, True) # True = Combine with view transform
                painter.drawImage(0, 0, layer.image)
                
                # Reset transform for next iteration
                view_transform = QTransform()
                view_transform.translate(self.offset_x, self.offset_y)
                view_transform.scale(self.scale_factor, self.scale_factor)
                painter.setTransform(view_transform)
                
                # --- 3. DRAW TRANSFORM BOUNDS ---
                if self.current_tool in ["move", "rotate", "scale"] and i == self.active_layer_index:
                    # Map the rect through the transform so the box rotates with the image
                    mapped_rect = transform.map(QPolygonF(QRectF(0, 0, layer.image.width(), layer.image.height())))
                    
                    color = "#00aaff" # Blue for Move
                    if self.current_tool == "rotate": color = "#ffaa00" # Orange for Rotate
                    elif self.current_tool == "scale": color = "#00ff00" # Green for Scale
                    
                    pen = QPen(QColor(color), 2)
                    painter.setPen(pen)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawPolygon(mapped_rect)
                
                # Draw Pivot Point (Center of object)
                if self.current_tool == "rotate" and i == self.active_layer_index:
                    pivot = transform.map(QPointF(layer.image.width()/2, layer.image.height()/2))
                    painter.setBrush(Qt.GlobalColor.white)
                    painter.setPen(Qt.GlobalColor.black)
                    painter.drawEllipse(pivot, 5, 5)
                    
                    
        # --- DRAW BRUSH CURSOR ---
        # Draw this LAST so it floats above everything
        if self.show_cursor_circle and self.current_tool in ["brush", "eraser"]:
            painter.setTransform(view_transform) # Use View Transform (Zoom/Pan) but NOT Layer Transform
            
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # Visual: Thin grey line ensures visibility on dark AND light backgrounds
            # A common trick is to draw two circles: one black, one white (offset)
            pen = QPen(QColor(0, 0, 0, 150), 1) # Black, semi-transparent
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Draw!
            # Radius is size / 2
            radius = self.brush_size / 2
            painter.drawEllipse(self.cursor_pos, radius, radius)
            
            # Optional: Inner white ring for better visibility on dark colors
            pen.setColor(QColor(255, 255, 255, 150))
            painter.setPen(pen)
            # Draw slightly smaller to create a "double outline" effect
            painter.drawEllipse(self.cursor_pos, radius - 1, radius - 1)
            self.update()
                    
        # --- DRAW SELECTION ---
        if not self.selection_path.isEmpty():
            painter.setOpacity(1.0)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            pen = QPen(Qt.GlobalColor.white, 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self.selection_path)
            
        # Draw live lasso line
        if self.current_tool in ["lasso", "poly_lasso"] and self.lasso_points:
            pen = QPen(Qt.GlobalColor.yellow, 1, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.drawPolyline(QPolygonF([QPointF(p) for p in self.lasso_points]))
            
    def map_to_canvas(self, widget_point):
        x = (widget_point.x() - self.offset_x) / self.scale_factor
        y = (widget_point.y() - self.offset_y) / self.scale_factor
        return QPointF(x, y)
    
    def mousePressEvent(self, event):
        # 1. Handle Pan (Spacebar / Middle Click)
        if event.modifiers() == Qt.KeyboardModifier.ShiftModifier or event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return

        canvas_pos = self.map_to_canvas(event.pos())
        self.last_mouse_pos = event.pos() 
        
        if self.current_tool in ["move", "rotate", "scale"]:
            active_layer = self.layers[self.active_layer_index]
            if not self.selection_path.isEmpty() and not active_layer.is_floating:
                # Lift it!
                success = self.lift_selection_to_layer()
                if success:
                    print(" Lifted Selection to Floating Layer")
            self.drawing = True 
            self.transform_start_pos = event.pos()

        elif self.current_tool == "lasso":
            self.is_selecting = True
            self.selection_path = QPainterPath()
            self.lasso_points = [canvas_pos]

        elif self.current_tool == "poly_lasso":
            if not self.lasso_points:
                self.selection_path = QPainterPath()
            self.lasso_points.append(canvas_pos)
            self.update()

        elif self.current_tool in ["brush", "eraser"]:
            self.drawing = True
            if 0 <= self.active_layer_index < len(self.layers):
                self.history.save_state(self.active_layer_index, self.layers[self.active_layer_index].image)
            self.last_canvas_pos = canvas_pos
            self.pressure = 1.0
        
        canvas_pos = self.map_to_canvas(event.pos())
        self.last_mouse_pos = event.pos() # Screen coords for transform deltas
        
        if self.current_tool == "move":
            self.drawing = True
            self.transform_start_pos = event.pos()
            
        elif self.current_tool == "lasso":
            self.is_selecting = True
            self.selection_path = QPainterPath()
            self.lasso_points = [canvas_pos]
            
        elif self.current_tool == "poly_lasso":
            # Don't clear path on every click, only on first point
            if not self.lasso_points:
                self.selection_path = QPainterPath()
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
        self.cursor_pos = canvas_pos # Save for the paintEvent
        self.show_cursor_circle = True
        
        if self.panning:
            delta = event.pos() - self.last_mouse_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_mouse_pos = event.pos()
            self.update()
            
        elif self.drawing and self.current_tool == "move":
            # TRANSFORM LOGIC
            delta = event.pos() - self.transform_start_pos
            layer = self.layers[self.active_layer_index]
            
            if event.buttons() & Qt.MouseButton.RightButton:
                # Rotate
                layer.rotation += delta.x() * 0.5
            elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Scale
                scale_change = delta.x() * 0.01
                layer.scale_x += scale_change
                layer.scale_y += scale_change
            else:
                # Move
                layer.x += delta.x() / self.scale_factor
                layer.y += delta.y() / self.scale_factor
                
            self.transform_start_pos = event.pos()
            self.update()
            
        elif self.current_tool == "lasso" and self.is_selecting:
            self.lasso_points.append(canvas_pos)
            self.update()
                    
        elif self.current_tool == "poly_lasso":
            self.update() # Just update for visual feedback
            
        elif self.drawing and self.current_tool in ["brush", "eraser"]:
            self.draw_stroke(canvas_pos)
            
        elif self.drawing and self.current_tool in ["move", "rotate", "scale"]:
            # --- TRANSFORM LOGIC ---
            delta = event.pos() - self.transform_start_pos
            layer = self.layers[self.active_layer_index]
            
            # 1. MOVE TOOL (V)
            if self.current_tool == "move":
                if event.buttons() & Qt.MouseButton.RightButton:
                    layer.rotation += delta.x() * 0.5
                elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    change = delta.x() * 0.01
                    layer.scale_x += change
                    layer.scale_y += change
                else:
                    layer.x += delta.x() / self.scale_factor
                    layer.y += delta.y() / self.scale_factor

            # 2. ROTATE TOOL (R)
            elif self.current_tool == "rotate":
                layer.rotation += delta.x() * 0.5
                
            # 3. SCALE TOOL (Ctrl+T)
            elif self.current_tool == "scale":
                # Uniform scale based on drag distance
                change = delta.x() * 0.01
                layer.scale_x += change
                layer.scale_y += change

            self.transform_start_pos = event.pos()
            self.update()
            
        self.update()
        
    def leaveEvent(self, event):
        self.show_cursor_circle = False
        self.update()
        super().leaveEvent(event)
            
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
        
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Poly Lasso Confirm
        if self.current_tool == "poly_lasso" and key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            if len(self.lasso_points) > 2:
                self.selection_path.addPolygon(QPolygonF([QPointF(p) for p in self.lasso_points]))
                self.selection_path.closeSubpath()
            self.lasso_points = []
            self.update()
            
        if self.current_tool in ["move", "rotate", "scale"] and key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.commit_transform()
            print("✅ Transform Committed")
            # Optional: Switch back to brush after commit
            self.parent().station.set_tool("brush")
            
        # Commit Transform
        if self.current_tool == "move" and key in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.commit_transform()
            print("✅ Move Committed")
            
    def lift_selection_to_layer(self):
        if not (0 <= self.active_layer_index < len(self.layers)): return
        source_layer = self.layers[self.active_layer_index]
        
        # 1. Determine the Crop Area
        if not self.selection_path.isEmpty():
            # Use the specific selection
            crop_rect = self.selection_path.boundingRect().toRect()
        else:
            # No selection? Use the "Content Bounds" (Auto-Crop)
            # We scan the alpha channel to find where the pixels actually are
            # (Simplification: For now, we'll just use the whole frame if no selection, 
            #  but in v7 we would scan pixels. Let's stick to Selection for now.)
            return False # Only lift if selected for this step
            
        if crop_rect.isEmpty(): return False

        # 2. Create the "Floating" Layer
        # It is exactly the size of the selection!
        floating_layer = Layer("Floating Object", crop_rect.width(), crop_rect.height())
        floating_layer.is_floating = True
        
        # 3. Copy pixels from Source -> Float
        source_rect = crop_rect
        # We define where on the float image we paste to
        dest_point = QPoint(0, 0)
        
        painter = QPainter(floating_layer.image)
        painter.drawImage(dest_point, source_layer.image, source_rect)
        painter.end()
        
        eraser = QPainter(source_layer.image)
        eraser.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        # If we have a complex path, use that. Otherwise use rect.
        if not self.selection_path.isEmpty():
            eraser.setClipPath(self.selection_path)
            eraser.fillRect(source_layer.image.rect(), Qt.GlobalColor.white) # Color doesn't matter, mode is Clear
        else:
            eraser.eraseRect(crop_rect)
        eraser.end()
        
        floating_layer.x = crop_rect.x()
        floating_layer.y = crop_rect.y()
        
        # 6. Add to stack and Select it
        self.layers.append(floating_layer)
        self.active_layer_index = len(self.layers) - 1
        
        # Clear selection path (the "ants" are now the layer bounds)
        self.selection_path = QPainterPath()
        self.update()
        return True
            
        # Undo/Redo
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if key == Qt.Key.Key_Z:
                self.history.undo(self.layers)
                self.update()
            elif key == Qt.Key.Key_Y:
                self.history.redo(self.layers)
                self.update()
            #Transform Tool Shortcut
            #elif key == Qt.Key.Key_T:
            #    self.parent().station.set_tool("transform")
                
        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_T:
            if self.parent():
                self.parent().station.set_tool("scale")
        
        self.handle_shortcuts(key)
        
    def handle_shortcuts(self, key):
        if not self.parent(): return
        if key == Qt.Key.Key_B: self.parent().station.set_tool("brush")
        elif key == Qt.Key.Key_E: self.parent().station.set_tool("eraser")
        elif key == Qt.Key.Key_V: self.parent().station.set_tool("move")
        elif key == Qt.Key.Key_L: self.parent().station.set_tool("lasso")
        elif key == Qt.Key.Key_P: self.parent().station.set_tool("poly_lasso")
        elif key == Qt.Key.Key_R: self.parent().station.set_tool("rotate")
        elif key == Qt.Key.Key_Delete:
            if self.delete_active_layer():
                print(" Layer Deleted")
                if hasattr(self.parent(), 'layer_panel'): 
                    self.parent().layer_panel.refresh_list()
        
        elif key == Qt.Key.Key_Escape:
            self.selection_path = QPainterPath()
            self.lasso_points = []
            self.update()
            
        elif key == Qt.Key.Key_BracketLeft:
            self.brush_size = max(1, self.brush_size - 5)
            self.parent().station.slider_size.setValue(self.brush_size)
        elif key == Qt.Key.Key_BracketRight: 
            self.brush_size = min(100, self.brush_size + 5)
            self.parent().station.slider_size.setValue(self.brush_size)
            
    def commit_transform(self):
        if not (0 <= self.active_layer_index < len(self.layers)): return
        layer = self.layers[self.active_layer_index]
        if layer.x == 0 and layer.y == 0 and layer.rotation == 0 and layer.scale_x == 1: return
        else:
            print("🔨 Merging Floating Object Down...")
            self.history.save_state(self.active_layer_index - 1, self.layers[self.active_layer_index - 1].image)
            
            # The layer BELOW is the target
            target_layer = self.layers[self.active_layer_index - 1]
            
            # Create a painter on the TARGET (Background/Original Layer)
            painter = QPainter(target_layer.image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Recreate the Float Layer's Matrix
            transform = QTransform()
            # Move to where the float layer is visually
            transform.translate(layer.x, layer.y)
            # Pivot around the FLOAT layer's center (Object Center!)
            center_x = layer.image.width() / 2
            center_y = layer.image.height() / 2
            transform.translate(center_x, center_y)
            transform.rotate(layer.rotation)
            transform.scale(layer.scale_x, layer.scale_y)
            transform.translate(-center_x, -center_y)
            
            painter.setTransform(transform)
            painter.drawImage(0, 0, layer.image)
            painter.end()
            
            # Delete the floating layer
            del self.layers[self.active_layer_index]
            self.active_layer_index -= 1
            
            self.update()
        
    def draw_stroke(self, current_point):
        if not (0 <= self.active_layer_index < len(self.layers)): return
        layer = self.layers[self.active_layer_index]
        if not layer.visible: return
        
        # 1. Build Layer Matrix
        transform = QTransform()
        transform.translate(layer.x, layer.y)
        center_x = layer.image.width() / 2
        center_y = layer.image.height() / 2
        transform.translate(center_x, center_y)
        transform.rotate(layer.rotation)
        transform.scale(layer.scale_x, layer.scale_y)
        transform.translate(-center_x, -center_y)
        
        # 2. Invert to map Mouse coords -> Image coords
        inverted_transform, _ = transform.inverted()
        local_start = inverted_transform.map(self.last_canvas_pos)
        local_end = inverted_transform.map(current_point)
        
        painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 3. Clip to Selection
        if not self.selection_path.isEmpty():
            # Map the selection path to layer space too
            mapped_path = inverted_transform.map(self.selection_path)
            painter.setClipPath(mapped_path)
            
        size = self.brush_size * self.pressure
        color = QColor(self.brush_color)
        if self.is_eraser:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        else:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        
        pen = QPen(color, size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(local_start, local_end)
        
        self.last_canvas_pos = current_point
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