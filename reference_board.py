"""
Reference Board - Infinite Canvas for Reference Images and Notes
This is like a digital cork board for artists.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPen, QPixmap, QWheelEvent, QCursor
from PyQt6.QtCore import Qt, QPoint, QRect, QSize, pyqtSignal
import json

from reference_items import ReferenceItem, ImageItem, StickyNote


class ReferenceBoard(QWidget):
    """
    The infinite canvas where reference items live.
    Similar to your Canvas class, but for reference materials.
    """
    
    items_changed = pyqtSignal()  # Notify when items are added/removed
    
    def __init__(self):
        super().__init__()
        self.setObjectName("ReferenceBoard")
        self.setAcceptDrops(True)  # Enable drag & drop from file system
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # --- ITEMS ---
        self.items = []  # List of ReferenceItem objects
        
        # --- VIEW STATE ---
        self.view_offset = QPoint(0, 0)  # Pan offset
        self.view_scale = 1.0            # Zoom level
        
        # --- BACKGROUND COLOR ---
        self.bg_colors = {
            "light_gray": "#E8E8E8",
            "dark_gray": "#3D3D3D",
            "white": "#FFFFFF"
        }
        self.current_bg = "light_gray"
        
        # --- INTERACTION STATE ---
        self.is_panning = False
        self.pan_start = QPoint()
        
        self.dragging_item = None
        self.drag_offset = QPoint()
        
        self.selected_items = []
        
        # --- IMAGE PREVIEW STATE ---
        self.preview_pixmap = None      # The image being previewed
        self.preview_pos = QPoint()     # Mouse position
        self.preview_size = QSize()     # Current preview size
        self.preview_path = None        # Path to image being previewed
        
        # --- RESIZE STATE ---
        self.resizing_item = None       # Item being resized
        self.resize_handle = None       # Which handle (nw, ne, sw, se, etc.)
        self.resize_start_pos = QPoint()
        self.resize_start_size = QSize()
        self.resize_start_item_pos = QPoint()
        
        # --- STYLING ---
        self.update_background_color()
        
        self.setMouseTracking(True)
        
    # --- DRAWING ---
    
    def paintEvent(self, event):
        """Draw the infinite canvas grid and all items."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw grid background
        self.draw_grid(painter)
        
        # Draw all items (sorted by z_index)
        sorted_items = sorted(self.items, key=lambda x: x.z_index)
        for item in sorted_items:
            item.draw(painter, self.view_offset)
        
        # Draw image preview if in preview mode
        if self.preview_pixmap:
            self.draw_preview(painter)
    
    def draw_grid(self, painter):
        """Draw the infinite grid pattern."""
        grid_size = 35
        
        # Calculate visible grid range
        offset_x = self.view_offset.x() % grid_size
        offset_y = self.view_offset.y() % grid_size
        
        painter.setPen(QPen(QColor("#D0D0D0"), 1))
        
        # Vertical lines
        x = offset_x
        while x < self.width():
            painter.drawLine(x, 0, x, self.height())
            x += grid_size
        
        # Horizontal lines
        y = offset_y
        while y < self.height():
            painter.drawLine(0, y, self.width(), y)
            y += grid_size
    
    def draw_preview(self, painter):
        """Draw the image preview that follows the mouse."""
        # Draw semi-transparent preview
        painter.setOpacity(0.7)
        
        # Center preview on mouse
        half_size = QSize(self.preview_size.width() // 2, self.preview_size.height() // 2)
        draw_pos = self.preview_pos - QPoint(half_size.width(), half_size.height())
        
        painter.drawPixmap(draw_pos, self.preview_pixmap)
        
        # Draw border
        painter.setOpacity(1.0)
        painter.setPen(QPen(QColor("#4A90E2"), 2, Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(QRect(draw_pos, self.preview_size))
        
        # Draw size label
        painter.setPen(QColor("#000000"))
        painter.drawText(
            draw_pos.x(),
            draw_pos.y() - 5,
            f"{self.preview_size.width()}x{self.preview_size.height()} px"
        )
    
    # --- ITEM MANAGEMENT ---
    
    def set_background_color(self, color_name: str):
        """Change the background color."""
        if color_name in self.bg_colors:
            self.current_bg = color_name
            self.update_background_color()
    
    def update_background_color(self):
        """Apply the current background color."""
        color = self.bg_colors.get(self.current_bg, "#E8E8E8")
        self.setStyleSheet(f"""
            #ReferenceBoard {{
                background-color: {color};
            }}
        """)
        self.update()
    
    def duplicate_selected(self):
        """Duplicate all selected items (Ctrl+D)."""
        if not self.selected_items:
            return
        
        new_items = []
        offset = QPoint(20, 20)  # Offset duplicates slightly
        
        for item in self.selected_items:
            # Create a copy
            if isinstance(item, ImageItem):
                new_item = ImageItem(item.pos + offset, item.image_path)
                new_item.resize_to(QSize(item.size))
            elif isinstance(item, StickyNote):
                new_item = StickyNote(
                    item.pos + offset,
                    QSize(item.size),
                    item.text,
                    item.color_name
                )
            else:
                continue
            
            new_item.z_index = len(self.items) + len(new_items)
            new_items.append(new_item)
        
        # Add all new items
        self.items.extend(new_items)
        
        # Select only the new items
        self.clear_selection()
        for item in new_items:
            item.selected = True
            self.selected_items.append(item)
        
        self.items_changed.emit()
        self.update()
    
    def add_image(self, image_path: str, pos: QPoint = None):
        """Start image preview mode instead of directly adding."""
        self.start_image_preview(image_path)
    
    def start_image_preview(self, image_path: str):
        """Start previewing an image before placing it."""
        # Load the full image
        original_pixmap = QPixmap(image_path)
        
        # Scale to max 1200px
        if original_pixmap.width() > 1200 or original_pixmap.height() > 1200:
            self.preview_size = original_pixmap.size().scaled(
                1200, 1200,
                Qt.AspectRatioMode.KeepAspectRatio
            )
        else:
            self.preview_size = original_pixmap.size()
        
        # Create scaled preview
        self.preview_pixmap = original_pixmap.scaled(
            self.preview_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.preview_path = image_path
        self.preview_pos = self.mapFromGlobal(QCursor.pos())
        
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.update()
    
    def finalize_image_preview(self):
        """Place the previewed image at current position."""
        if self.preview_pixmap:
            # Convert screen position to world position
            world_pos = self.screen_to_world(self.preview_pos)
            
            # Offset to center the image on click point
            half_size = QSize(self.preview_size.width() // 2, self.preview_size.height() // 2)
            world_pos -= QPoint(half_size.width(), half_size.height())
            
            # Create the item with the current preview size
            item = ImageItem(world_pos, self.preview_path)
            item.resize_to(self.preview_size)
            item.z_index = len(self.items)
            self.items.append(item)
            self.items_changed.emit()
            
            # Clear preview
            self.preview_pixmap = None
            self.preview_path = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
    
    def cancel_image_preview(self):
        """Cancel image preview."""
        self.preview_pixmap = None
        self.preview_path = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()
    
    def add_sticky_note(self, pos: QPoint = None, text: str = ""):
        """Add a sticky note to the board."""
        if pos is None:
            pos = self.screen_to_world(self.rect().center())
        
        item = StickyNote(pos, text=text)
        item.z_index = len(self.items)
        self.items.append(item)
        self.items_changed.emit()
        self.update()
        
        return item
    
    def delete_selected(self):
        """Remove all selected items."""
        self.items = [item for item in self.items if not item.selected]
        self.selected_items.clear()
        self.items_changed.emit()
        self.update()
    
    def clear_selection(self):
        """Deselect all items."""
        for item in self.items:
            item.selected = False
        self.selected_items.clear()
        self.update()
    
    # --- COORDINATE CONVERSION ---
    
    def screen_to_world(self, screen_point: QPoint) -> QPoint:
        """Convert screen coordinates to world coordinates."""
        return QPoint(
            int((screen_point.x() - self.view_offset.x()) / self.view_scale),
            int((screen_point.y() - self.view_offset.y()) / self.view_scale)
        )
    
    def world_to_screen(self, world_point: QPoint) -> QPoint:
        """Convert world coordinates to screen coordinates."""
        return QPoint(
            int(world_point.x() * self.view_scale + self.view_offset.x()),
            int(world_point.y() * self.view_scale + self.view_offset.y())
        )
    
    # --- MOUSE INTERACTION ---
    
    def mousePressEvent(self, event):
        """Handle mouse press - select or start dragging items."""
        print(f"DEBUG: mousePressEvent - button: {event.button()}")
        
        # If in preview mode, finalize on click
        if self.preview_pixmap:
            print("DEBUG: In preview mode")
            if event.button() == Qt.MouseButton.LeftButton:
                print("DEBUG: Finalizing image preview")
                self.finalize_image_preview()
            elif event.button() == Qt.MouseButton.RightButton:
                print("DEBUG: Canceling image preview")
                self.cancel_image_preview()
            return
        
        if event.button() == Qt.MouseButton.MiddleButton:
            # Middle mouse = Pan
            self.is_panning = True
            self.pan_start = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        
        if event.button() == Qt.MouseButton.LeftButton:
            screen_pos = event.position().toPoint()
            
            # Check if clicking delete button on any selected item
            for item in reversed(self.items):
                if item.selected:
                    if isinstance(item, ImageItem) or isinstance(item, StickyNote):
                        delete_rect = item.get_delete_button_rect(self.view_offset)
                        if delete_rect.contains(screen_pos):
                            # Delete this item
                            self.items.remove(item)
                            if item in self.selected_items:
                                self.selected_items.remove(item)
                            self.items_changed.emit()
                            self.update()
                            return
            
            # Check if clicking on a resize handle
            for item in reversed(self.items):
                if isinstance(item, ImageItem) and item.selected:
                    handle = item.get_resize_handle(screen_pos, self.view_offset)
                    if handle:
                        self.resizing_item = item
                        self.resize_handle = handle
                        self.resize_start_pos = screen_pos
                        self.resize_start_size = QSize(item.size)
                        self.resize_start_item_pos = QPoint(item.pos)
                        return
            
            world_pos = self.screen_to_world(screen_pos)
            
            # Check if clicking on an item (reverse order = top first)
            clicked_item = None
            for item in reversed(self.items):
                if item.contains(world_pos):
                    clicked_item = item
                    break
            
            if clicked_item:
                # Select this item
                if not event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self.clear_selection()
                
                clicked_item.selected = True
                self.selected_items.append(clicked_item)
                
                # Start dragging
                self.dragging_item = clicked_item
                self.drag_offset = world_pos - clicked_item.pos
                
                self.update()
            else:
                # Clicked empty space - clear selection
                self.clear_selection()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move - pan, drag items, or resize."""
        screen_pos = event.position().toPoint()
        
        # Update preview position if in preview mode
        if self.preview_pixmap:
            self.preview_pos = screen_pos
            self.update()
            return
        
        # Pan mode
        if self.is_panning:
            delta = screen_pos - self.pan_start
            self.view_offset += delta
            self.pan_start = screen_pos
            self.update()
            return
        
        # Resize mode
        if self.resizing_item:
            self.handle_resize(screen_pos)
            return
        
        # Drag mode
        if self.dragging_item:
            world_pos = self.screen_to_world(screen_pos)
            self.dragging_item.pos = world_pos - self.drag_offset
            self.update()
            return
        
        # Update cursor based on hover
        self.update_cursor(screen_pos)
    
    def handle_resize(self, screen_pos: QPoint):
        """Handle resizing an image item."""
        delta = screen_pos - self.resize_start_pos
        
        handle = self.resize_handle
        item = self.resizing_item
        
        # Calculate new size and position based on handle
        new_size = QSize(self.resize_start_size)
        new_pos = QPoint(self.resize_start_item_pos)
        
        if 'e' in handle:  # East (right edge)
            new_size.setWidth(max(50, self.resize_start_size.width() + delta.x()))
        if 'w' in handle:  # West (left edge)
            new_width = max(50, self.resize_start_size.width() - delta.x())
            new_pos.setX(self.resize_start_item_pos.x() + (self.resize_start_size.width() - new_width))
            new_size.setWidth(new_width)
        if 's' in handle:  # South (bottom edge)
            new_size.setHeight(max(50, self.resize_start_size.height() + delta.y()))
        if 'n' in handle:  # North (top edge)
            new_height = max(50, self.resize_start_size.height() - delta.y())
            new_pos.setY(self.resize_start_item_pos.y() + (self.resize_start_size.height() - new_height))
            new_size.setHeight(new_height)
        
        # Apply resize
        item.pos = new_pos
        item.resize_to(new_size)
        self.update()
    
    def update_cursor(self, screen_pos: QPoint):
        """Update cursor based on what's under the mouse."""
        # Check if hovering over resize handle
        for item in reversed(self.items):
            if isinstance(item, ImageItem) and item.selected:
                handle = item.get_resize_handle(screen_pos, self.view_offset)
                if handle:
                    # Set cursor based on handle type
                    cursor_map = {
                        'nw': Qt.CursorShape.SizeFDiagCursor,
                        'ne': Qt.CursorShape.SizeBDiagCursor,
                        'sw': Qt.CursorShape.SizeBDiagCursor,
                        'se': Qt.CursorShape.SizeFDiagCursor,
                        'n': Qt.CursorShape.SizeVerCursor,
                        's': Qt.CursorShape.SizeVerCursor,
                        'e': Qt.CursorShape.SizeHorCursor,
                        'w': Qt.CursorShape.SizeHorCursor,
                    }
                    self.setCursor(cursor_map.get(handle, Qt.CursorShape.ArrowCursor))
                    return
        
        self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release - stop dragging/panning/resizing."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_item = None
            self.resizing_item = None
            self.resize_handle = None
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click - edit sticky notes."""
        if event.button() == Qt.MouseButton.LeftButton:
            screen_pos = event.position().toPoint()
            world_pos = self.screen_to_world(screen_pos)
            
            # Check if double-clicking on a sticky note
            for item in reversed(self.items):
                if isinstance(item, StickyNote) and item.contains(world_pos):
                    # Open edit dialog
                    from PyQt6.QtWidgets import QInputDialog
                    new_text, ok = QInputDialog.getMultiLineText(
                        self,
                        "Edit Sticky Note",
                        "Note text:",
                        item.text
                    )
                    
                    if ok:
                        item.text = new_text
                        self.update()
                    return
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel - zoom in/out OR resize preview."""
        # If in preview mode, resize the preview
        if self.preview_pixmap:
            # Zoom the preview size
            zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
            
            new_width = int(self.preview_size.width() * zoom_factor)
            new_height = int(self.preview_size.height() * zoom_factor)
            
            # Clamp to reasonable bounds
            new_width = max(50, min(new_width, 4000))
            new_height = max(50, min(new_height, 4000))
            
            self.preview_size = QSize(new_width, new_height)
            
            # Rescale preview pixmap
            original = QPixmap(self.preview_path)
            self.preview_pixmap = original.scaled(
                self.preview_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.update()
            return
        
        # Normal zoom of canvas
        # Get mouse position before zoom
        mouse_pos = event.position().toPoint()
        world_pos = self.screen_to_world(mouse_pos)
        
        # Zoom
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.view_scale = max(0.1, min(self.view_scale * zoom_factor, 5.0))
        
        # Adjust offset to zoom toward mouse
        new_screen_pos = self.world_to_screen(world_pos)
        self.view_offset += mouse_pos - new_screen_pos
        
        self.update()
    
    # --- DRAG & DROP FROM FILE SYSTEM ---
    
    def dragEnterEvent(self, event):
        """Accept image files being dragged in."""
        print("DEBUG: dragEnterEvent triggered")
        if event.mimeData().hasUrls():
            print(f"DEBUG: Has URLs: {event.mimeData().urls()}")
            event.acceptProposedAction()
        else:
            print("DEBUG: No URLs in drag data")
    
    def dropEvent(self, event):
        """Handle dropped files - start image preview."""
        print("DEBUG: dropEvent triggered")
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            print(f"DEBUG: Dropped file: {file_path}")
            
            # Check if it's an image
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                print(f"DEBUG: Starting image preview for: {file_path}")
                # Start preview mode
                self.start_image_preview(file_path)
                break  # Only handle first image
            else:
                print(f"DEBUG: File is not an image: {file_path}")
        
        event.acceptProposedAction()
    
    # --- KEYBOARD SHORTCUTS ---
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        # Cancel preview mode
        if self.preview_pixmap and event.key() == Qt.Key.Key_Escape:
            self.cancel_image_preview()
            return
        
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        elif event.key() == Qt.Key.Key_Escape:
            self.clear_selection()
        elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+D = Duplicate
            self.duplicate_selected()
        elif event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Select all
            for item in self.items:
                item.selected = True
                if item not in self.selected_items:
                    self.selected_items.append(item)
            self.update()
    
    # --- SAVE / LOAD ---
    
    def save_board(self, file_path: str):
        """Save the board state to a JSON file."""
        data = {
            "version": "1.0",
            "view_offset": {"x": self.view_offset.x(), "y": self.view_offset.y()},
            "view_scale": self.view_scale,
            "items": [item.to_dict() for item in self.items]
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Board saved to {file_path}")
    
    def load_board(self, file_path: str):
        """Load a board state from a JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Restore view
        self.view_offset = QPoint(data["view_offset"]["x"], data["view_offset"]["y"])
        self.view_scale = data["view_scale"]
        
        # Restore items
        self.items.clear()
        for item_data in data["items"]:
            item_type = item_data["type"]
            
            if item_type == "ImageItem":
                item = ImageItem.from_dict(item_data)
            elif item_type == "StickyNote":
                item = StickyNote.from_dict(item_data)
            else:
                continue
            
            self.items.append(item)
        
        self.items_changed.emit()
        self.update()
        print(f"Board loaded from {file_path}")