from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import QPoint, QRect

class HistoryState:
    """
    Represents a single 'Undoable' action.
    Instead of saving the whole world, we save a 'Patch'.
    """
    def __init__(self, layer_index, rect, before_pixmap, after_pixmap):
        self.layer_index = layer_index
        self.rect = rect
        self.before = before_pixmap # The "Ghost" of what used to be there
        self.after = after_pixmap   # What you just drew

class HistoryManager:
    def __init__(self, canvas_ref):
        self.canvas = canvas_ref
        self.undo_stack = []
        self.redo_stack = []
        # Max steps to prevent infinite memory usage (Standard is 20-50)
        self.max_history = 50 

    def push_state(self, layer_idx, rect, before, after):
        """Saves a new action."""
        state = HistoryState(layer_idx, rect, before, after)
        self.undo_stack.append(state)
        
        # If we branch off (draw something new), the Redo future is lost
        self.redo_stack.clear()
        
        # Keep stack size manageable
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0) # Remove the oldest memory
            
        print(f"History Saved. Stack Size: {len(self.undo_stack)}")

    def undo(self):
        if not self.undo_stack:
            print("Nothing to Undo.")
            return
        
        # 1. Get the last action
        state = self.undo_stack.pop()
        self.redo_stack.append(state)
        
        # 2. Apply the 'Before' image patch
        self._apply_patch(state.layer_index, state.rect, state.before)
        print("Undid Action.")

    def redo(self):
        if not self.redo_stack:
            print("Nothing to Redo.")
            return
            
        # 1. Get the future action
        state = self.redo_stack.pop()
        self.undo_stack.append(state)
        
        # 2. Apply the 'After' image patch
        self._apply_patch(state.layer_index, state.rect, state.after)
        print("Redid Action.")

    def _apply_patch(self, layer_idx, rect, patch):
        """The Surgeon: Stitches the patch back onto the layer."""
        if 0 <= layer_idx < len(self.canvas.layers):
            target_layer = self.canvas.layers[layer_idx]
            
            # Draw the patch onto the specific spot
            painter = QPainter(target_layer.pixmap)
            # Use Source mode to replace pixels (handling transparency correctly)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.drawPixmap(rect.topLeft(), patch)
            painter.end()
            
            self.canvas.compose_layers()