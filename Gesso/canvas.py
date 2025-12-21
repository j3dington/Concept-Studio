import sys
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import (QPainter, QColor, QPen, QPixmap, QTabletEvent, 
                        QPolygon, QTransform, QImage)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QPointF, QSize

# --- LOCAL IMPORTS ---
from enums import ToolType
from layer import Layer
from history import HistoryManager 
from assets import (get_custom_cursor, get_round_cursor, get_soft_brush_pixmap,
                    load_custom_brush, create_outline_cursor)
from drawing_engine import DrawingEngine 

class Canvas(QWidget):
    tool_changed = pyqtSignal(object)
    layers_changed = pyqtSignal()
    color_changed = pyqtSignal(QColor)

    def __init__(self):
        super().__init__()
        self.setObjectName("Canvas")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        
        # --- THE WORKER ---
        self.engine = DrawingEngine() 
        
        # --- TOOL STATE ---
        self.current_tool = ToolType.BRUSH
        self.previous_tool = None # For Alt-switching
        
        # --- JITTER STATES ---
        self.jitter_size = 0.0
        self.jitter_angle = 0.0
        self.jitter_flow = 0.0
        self.jitter_scatter = 0.0
        self.jitter_hue = 0.0
        
        # --- VIEW STATE ---
        self.view_scale = 1.0        
        self.view_offset = QPoint(0, 0)
        
        # --- INPUT FLAGS ---
        self.is_drawing = False
        self.last_point = QPoint()
        self.last_pressure = 1.0
        
        # Hotkeys
        self.is_space_held = False   
        self.is_panning = False
        self.pan_start = QPoint()
        
        self.is_z_held = False       
        self.is_scrub_zooming = False
        self.zoom_start_pos = QPoint()
        self.zoom_start_scale = 1.0
        self.is_zoom_mode = False 
        
        # --- SELECTION STATE ---
        self.selection_rect = None   
        self.drag_start = None       
        self.lasso_path = []         
        self.floating_pixmap = None  
        self.original_floating_pixmap = None
        self.floating_pos = QPoint() 
        
        # --- LAYERS & HISTORY ---
        self.layers = []
        self.current_layer_index = -1
        self.display_pixmap = None
        self.history = HistoryManager(self)
        self.temp_layer_copy = None  
        self.stroke_rect = QRect()
        self.undo_stack = []
        self.undo_limit = 50
        
        self.stroke_bbox = QRect()
        
        self.init_layers(800, 600)
        self.refresh_cursor()

    def init_layers(self, width, height):
        size = QSize(width, height)
        bg = Layer("Background", size)
        bg.pixmap.fill(Qt.GlobalColor.white)
        self.layers.append(bg)
        l1 = Layer("Layer 1", size)
        l1.pixmap.fill(Qt.GlobalColor.transparent)
        self.layers.append(l1)
        self.current_layer_index = 1
        self.display_pixmap = QPixmap(size)
        self.compose_layers()

    # --- PROXY SETTERS (Pass data to Engine) ---
    def set_brush_size(self, size):
        self.engine.brush_size = size
        self.engine.update_brush_tip()
        self.refresh_cursor()

    def set_brush_color(self, color):
        self.engine.brush_color = color
        self.engine.update_brush_tip()
        
    def set_brush_shape(self, name):
        self.engine.brush_shape_name = name
        self.engine.update_brush_tip()
        self.refresh_cursor()

    def set_brush_opacity(self, value):
        c = self.engine.brush_color
        c.setAlphaF(value / 100.0)
        self.set_brush_color(c)
        
    def update_brush_tip(self):
        self.engine.update_brush_tip()

    def set_brush_flow(self, v): self.engine.brush_flow = v if v <= 1.0 else v/100.0
    def set_brush_spacing(self, v): self.engine.brush_spacing_factor = v
    
    def set_jitter_size(self, v):
        self.jitter_size = v          # Store it here for the UI
        self.engine.jitter_size = v   # Store it here for the drawing

    def set_jitter_angle(self, v):
        self.jitter_angle = v
        self.engine.jitter_angle = v

    def set_jitter_flow(self, v):
        self.jitter_flow = v
        self.engine.jitter_flow = v

    def set_jitter_scatter(self, v):
        self.jitter_scatter = v
        self.engine.jitter_scatter = v

    def set_jitter_hue(self, v):
        self.jitter_hue = v           # <--- This is the missing link!
        self.engine.jitter_hue = v
    # --- PROPERTIES ---
    @property
    def brush_size(self): return self.engine.brush_size
    
    @property
    def brush_color(self): return self.engine.brush_color
    
    @brush_color.setter
    def brush_color(self, color): self.engine.brush_color = color
    
    @property
    def brush_shape_name(self): return self.engine.brush_shape_name
    
    @property
    def brush_flow(self): return self.engine.brush_flow
    
    @property
    def brush_spacing_factor(self): return self.engine.brush_spacing_factor

    # --- JITTER SIZE ---
    @property
    def jitter_size(self):
        return self.engine.jitter_size

    @jitter_size.setter
    def jitter_size(self, value):
        self.engine.jitter_size = value

    # --- JITTER ANGLE ---
    @property
    def jitter_angle(self):
        return self.engine.jitter_angle

    @jitter_angle.setter
    def jitter_angle(self, value):
        self.engine.jitter_angle = value

    # --- JITTER HUE ---
    @property
    def jitter_hue(self):
        return self.engine.jitter_hue

    @jitter_hue.setter
    def jitter_hue(self, value):
        self.engine.jitter_hue = value
    
    # --- JITTER SCATTER ---
    @property
    def jitter_scatter(self): 
        return self.engine.jitter_scatter
        
    @jitter_scatter.setter
    def jitter_scatter(self, value):
        self.engine.jitter_scatter = value
        
    # --- JITTER FLOW ---
    @property
    def jitter_flow(self): 
        return self.engine.jitter_flow
        
    @jitter_flow.setter
    def jitter_flow(self, value):
        self.engine.jitter_flow = value
    
    @property
    def active_layer(self):
        return self.layers[self.current_layer_index]

    @active_layer.setter
    def active_layer(self, layer_obj):
        pass

    # --- TOOL SWITCHING ---
    def set_tool(self, tool: ToolType):
        if self.current_tool == ToolType.MOVE and self.floating_pixmap:
            self.anchor_selection()
        self.current_tool = tool
        self.refresh_cursor()
        self.tool_changed.emit(tool)

    # --- KEYBOARD INPUT (Restored) ---
    def keyPressEvent(self, event):
        # Alt Eyedropper
        if event.key() == Qt.Key.Key_Alt and self.current_tool != ToolType.EYEDROPPER:
            self.previous_tool = self.current_tool
            self.set_tool(ToolType.EYEDROPPER)
            
        # Space Pan
        elif event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self.is_space_held = True
            self.refresh_cursor()
            
        # Z Zoom
        elif event.key() == Qt.Key.Key_Z and not event.isAutoRepeat():
            self.is_z_held = True
            self.refresh_cursor()

        # Undo/Redo
        modifiers = event.modifiers()
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_Z:
                if modifiers & Qt.KeyboardModifier.ShiftModifier:
                    self.history.redo()
                else:
                    self.history.undo()
            elif event.key() == Qt.Key.Key_Y:
                self.history.redo()
                
        # Confirm Move
        elif event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            if self.current_tool == ToolType.MOVE:
                self.anchor_selection()
                self.update()

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            event.ignore()
            return
        
        if event.key() == Qt.Key.Key_Alt and self.previous_tool:
            self.set_tool(self.previous_tool)
            self.previous_tool = None
            
        elif event.key() == Qt.Key.Key_Space:
            self.is_space_held = False
            if not self.is_panning:
                self.refresh_cursor()
            
        elif event.key() == Qt.Key.Key_Z:
            self.is_z_held = False
            if not self.is_scrub_zooming:
                self.refresh_cursor()

    # --- MOUSE / TABLET INPUT ---
    def tabletEvent(self, event):
        pos = event.position().toPoint()
        pressure = event.pressure()
        if event.type() == QTabletEvent.Type.TabletPress:
            self.handle_press(pos, pressure)
        elif event.type() == QTabletEvent.Type.TabletMove:
            self.handle_move(pos, pressure, event.buttons())
        elif event.type() == QTabletEvent.Type.TabletRelease:
            self.handle_release(event.button())
        event.accept()

    def mousePressEvent(self, event):
        # 1. STOP: Don't let the engine touch ANYTHING yet.
        self.is_drawing = False 
        
        # 2. THE VAULT: Capture the state. 
        # We use .copy() to ensure it's a separate physical chunk of RAM.
        active_layer = self.layers[self.current_layer_index]
        self.pre_stroke_full_image = active_layer.pixmap.toImage().copy()
        
        # 3. VERIFY: Ensure the backup exists before proceeding
        if self.pre_stroke_full_image.isNull():
            print("CRITICAL: Backup failed! Aborting stroke to prevent ghosts.")
            return

        # 4. START: Only NOW do we let the ink flow.
        pos = event.position().toPoint()
        self.is_drawing = True
        self.handle_press(pos, 1.0)
            
    def mouseMoveEvent(self, event):
        if not hasattr(self, 'stroke_bbox'): return
        
        pos = event.position().toPoint()
        
        # FIX: We ask the engine for its 'Max Reach'
        margin = self.engine.max_reach
        
        new_rect = QRect(pos.x() - margin, pos.y() - margin, 
                         margin * 2, margin * 2)
        
        self.stroke_bbox = self.stroke_bbox.united(new_rect)
        self.handle_move(pos, 1.0, event.buttons())
    
    def mouseReleaseEvent(self, event):
        if not self.is_drawing: return
        self.is_drawing = False
        
        self.handle_release(event.button())
        
        # Push the FULL image onto the stack
        self.undo_stack.append(self.pre_stroke_full_image)
        
        # Memory Management: Keep only the last 20 full images
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)
            
    def enterEvent(self, event):
        self.setFocus()
        super().enterEvent(event)

    def handle_press(self, pos, pressure):
        self.setFocus()
        
        # 1. Panning / Zooming Overrides
        if self.is_space_held or self.current_tool == ToolType.PAN:
            self.is_panning = True
            self.pan_start = pos
            self.refresh_cursor()
            return
        if self.is_z_held or self.current_tool == ToolType.ZOOM: # Assuming ZOOM enum exists
            self.is_scrub_zooming = True
            self.zoom_start_pos = pos
            self.zoom_start_scale = self.view_scale
            self.setCursor(Qt.CursorShape.BlankCursor)
            return

        world_pos = self.to_world(pos)
        self.last_point = world_pos
        self.last_pressure = pressure
        self.engine.dist_to_next_dot = 0.0 
        
        # 2. RESTORED: Eyedropper
        if self.current_tool == ToolType.EYEDROPPER:
            self.color_picker(world_pos)
            return
            
        # 3. RESTORED: Fill Tool
        if self.current_tool == ToolType.FILL:
            # We call the engine, but we need to pass a snapshot for undo first
            if self.active_layer:
                self.history.push_state(self.current_layer_index, self.active_layer.pixmap.rect(), 
                                        self.active_layer.pixmap.copy(), None) # simplified undo
                self.engine.flood_fill(self.active_layer.pixmap, world_pos, self.engine.brush_color)
                self.compose_layers()
            return

        # 4. Selection Start
        if self.current_tool == ToolType.MARQUEE:
            if self.floating_pixmap: self.anchor_selection()
            self.selection_rect = QRect(world_pos, world_pos)
            self.drag_start = world_pos
            self.lasso_path = []
            self.update()
            return
            
        if self.current_tool == ToolType.LASSO:
            if self.floating_pixmap: self.anchor_selection()
            self.selection_rect = None
            self.lasso_path = [world_pos]
            self.update()
            return

        # 5. Drawing Start
        self.is_drawing = True
        if self.current_tool in [ToolType.BRUSH, ToolType.ERASER] and self.active_layer:
            self.temp_layer_copy = self.active_layer.pixmap.copy()
            self.stroke_rect = QRect(world_pos, world_pos)
            self.engine.draw_line(
                self.active_layer.pixmap, world_pos, world_pos, 
                pressure, pressure, 
                is_eraser=(self.current_tool == ToolType.ERASER)
            )
            self.update()
            
    def undo(self):
        if not self.undo_stack: 
            return
        
        # 1. Pop the backup
        backup_image = self.undo_stack.pop()
        active_layer = self.layers[self.current_layer_index]
        
        # 2. THE FIX: Physically destroy the old pixmap to clear any 'sticky' pixels
        active_layer.pixmap = QPixmap.fromImage(backup_image)
        
        # 3. THE SCRUB: Force the widget to ignore its cached drawing and start over
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        self.compose_layers()
        self.update() # This triggers a full repaint of the widget
        
    def handle_move(self, pos, pressure, buttons):
        if self.is_panning:
            self.view_offset += (pos - self.pan_start)
            self.pan_start = pos
            self.update()
            return
        if self.is_scrub_zooming:
            delta_x = pos.x() - self.zoom_start_pos.x()
            new_scale = max(0.1, min(self.zoom_start_scale * (1.0 + delta_x * 0.005), 5.0))
            center = self.rect().center()
            old_world = (center - self.view_offset) / self.view_scale 
            self.view_scale = new_scale
            self.view_offset = center - (old_world * self.view_scale)
            self.update()
            return

        if (buttons & Qt.MouseButton.LeftButton):
            world_pos = self.to_world(pos)
            
            # Drawing
            if self.is_drawing and self.current_tool in [ToolType.BRUSH, ToolType.ERASER]:
                self.engine.draw_line(
                    self.active_layer.pixmap, self.last_point, world_pos, 
                    self.last_pressure, pressure, 
                    is_eraser=(self.current_tool == ToolType.ERASER)
                )
                r = QRect(self.last_point, world_pos).normalized().adjusted(-50,-50,50,50)
                self.stroke_rect = self.stroke_rect.united(r)
                self.compose_layers()
                
            # Selection Drag
            elif self.current_tool == ToolType.MARQUEE and self.drag_start:
                self.selection_rect = QRect(self.drag_start, world_pos).normalized()
                self.update()
            elif self.current_tool == ToolType.LASSO:
                self.lasso_path.append(world_pos)
                self.update()
                
            # Move Tool
            elif self.current_tool == ToolType.MOVE and self.floating_pixmap:
                self.floating_pos += (world_pos - self.last_point)
                self.update()
                
            self.last_point = world_pos
            self.last_pressure = pressure
            
            if self.current_tool != ToolType.BRUSH and self.current_tool != ToolType.ERASER:
                self.update()
    def handle_release(self, button):
        if self.is_panning:
            self.is_panning = False
            self.refresh_cursor()
            return
        
        if self.is_scrub_zooming:
            self.is_scrub_zooming= False
            self.refresh_cursor()
            return
        
        if button == Qt.MouseButton.LeftButton:
            self.is_drawing = False
            
            # Undo Commit for Brush
            if self.current_tool in [ToolType.BRUSH, ToolType.ERASER] and self.temp_layer_copy:
                final_rect = self.stroke_rect.intersected(self.active_layer.pixmap.rect())
                if not final_rect.isEmpty():
                    before = self.temp_layer_copy.copy(final_rect)
                    after = self.active_layer.pixmap.copy(final_rect)
                    self.history.push_state(self.current_layer_index, final_rect, before, after)
                self.temp_layer_copy = None
            
            
            self.compose_layers()

    def color_picker(self, pos):
        x, y = int(pos.x()), int(pos.y())

        if not (0 <= x < self.display_pixmap.width() and 0 <= y < self.display_pixmap.height()):
            return

        img = self.display_pixmap.toImage()
        pixel_color = QColor(img.pixel(x, y))

        if pixel_color.alpha() > 0:
            self.brush_color = pixel_color 
            
            self.color_changed.emit(pixel_color)
            print(f"Eyedropper set color to: {pixel_color.name()}")

    # --- Floating Selection Anchoring ---
    def anchor_selection(self):
        if self.floating_pixmap and self.active_layer:
            p = QPainter(self.active_layer.pixmap)
            p.drawPixmap(self.floating_pos, self.floating_pixmap)
            p.end()
            self.floating_pixmap = None
            self.compose_layers()

    # --- Rendering for Selections ---
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.translate(self.view_offset)
        p.scale(self.view_scale, self.view_scale)
        p.drawPixmap(0, 0, self.display_pixmap)
        
        # Draw Floating Selection
        if self.floating_pixmap:
            p.drawPixmap(self.floating_pos, self.floating_pixmap)
            
        # Draw Selection Outlines
        scale_inv = 1.0 / self.view_scale
        pen_b = QPen(Qt.GlobalColor.black, scale_inv, Qt.PenStyle.DashLine)
        pen_w = QPen(Qt.GlobalColor.white, scale_inv, Qt.PenStyle.DashLine)
        pen_w.setDashOffset(3)
        
        if self.selection_rect and not self.floating_pixmap:
            p.setPen(pen_w); p.drawRect(self.selection_rect)
            p.setPen(pen_b); p.drawRect(self.selection_rect)
            
        if self.lasso_path and not self.floating_pixmap:
            poly = QPolygon(self.lasso_path)
            p.setPen(pen_w); p.drawPolyline(poly)
            p.setPen(pen_b); p.drawPolyline(poly)
            

    # --- UTILS ---
    def to_world(self, screen_point):
        return QPoint(
            int((screen_point.x() - self.view_offset.x()) / self.view_scale),
            int((screen_point.y() - self.view_offset.y()) / self.view_scale)
        )        
    def refresh_cursor(self):
        """
        Updates the cursor icon based on the current state priority.
        Priority: Dragging > Holding Hotkey > Selected Tool > Default
        """
        if self.is_panning:
            self.setCursor(get_custom_cursor("cursor_grabbing", scale=0.4))
            return
        if self.is_space_held or self.current_tool == ToolType.PAN:
            self.setCursor(get_custom_cursor("cursor_grab", scale=0.4))
            return
        if self.is_zoom_mode or self.is_z_held:
            self.setCursor(get_custom_cursor("cursor_zoom", scale=0.4))
            return
        if self.current_tool in [ToolType.BRUSH, ToolType.ERASER]:
            if hasattr(self, 'engine'):
                visual_size = int(self.engine.brush_size * self.view_scale)
                
                if self.engine.brush_shape_name == "Soft":
                    self.setCursor(get_round_cursor(visual_size))
                else:
                    tip = self.engine.current_brush_tip
                    if tip:
                        self.setCursor(create_outline_cursor(tip, visual_size))
                    else:
                        self.setCursor(get_round_cursor(visual_size))
            else:
                self.setCursor(get_round_cursor(20))

        elif self.current_tool == ToolType.FILL:
            self.setCursor(get_custom_cursor("fill", scale=0.4))
            
        elif self.current_tool == ToolType.MOVE:
            self.setCursor(get_custom_cursor("move", scale=0.4))
            
        elif self.current_tool == ToolType.EYEDROPPER:
            self.setCursor(get_custom_cursor("eyedropper", scale=0.4))
            
        elif self.current_tool in [ToolType.MARQUEE, ToolType.LASSO]:
            self.setCursor(get_custom_cursor("crosshair", scale=0.4))
            
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def add_new_layer(self, name=None):
        new_name = name or f"Layer {len(self.layers)}"
        size = self.layers[0].pixmap.size()
        new_layer = Layer(new_name, size)
        new_layer.pixmap.fill(Qt.GlobalColor.transparent)
        self.layers.append(new_layer)
        self.current_layer_index = len(self.layers) - 1
        self.compose_layers()
        self.layers_changed.emit()

    def delete_active_layer(self):
        if len(self.layers) <= 1: return False
        del self.layers[self.current_layer_index]
        if self.current_layer_index >= len(self.layers):
            self.current_layer_index = len(self.layers) - 1
        self.compose_layers()
        self.layers_changed.emit()
        return True
    
    def set_active_layer(self, index):
        if 0 <= index < len(self.layers):
            self.current_layer_index = index
            self.layers_changed.emit()
            
    def toggle_layer_visibility(self, index):
        if 0 <= index < len(self.layers):
            layer = self.layers[index]
            layer.visible = not layer.visible
            self.compose_layers()
            
    def set_active_layer_opacity(self, opacity):
        layer = self.layers[self.current_layer_index]
        layer.opacity = opacity
        self.compose_layers()

    def set_active_layer_blend_mode(self, mode):
        layer = self.layers[self.current_layer_index]
        layer.blend_mode = mode
        self.compose_layers()

    def compose_layers(self):
        self.display_pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(self.display_pixmap)
        
        for layer in self.layers:
            if not layer.visible:
                continue
            
            painter.setOpacity(layer.opacity)
            
            if layer.blend_mode == "Multiply":
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
            elif layer.blend_mode == "Screen":
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
            elif layer.blend_mode == "Overlay":
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
            elif layer.blend_mode == "Add":
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
            else:
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # 3. DRAW
            painter.drawPixmap(0, 0, layer.pixmap)
            
        painter.end()
        self.update()