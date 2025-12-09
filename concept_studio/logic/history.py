"""
History Manager for Undo/Redo

Implements the Command Pattern:
- Saves snapshots of layer states
- Maintains undo and redo stacks
- Limits history to prevent memory overflow

"""

from collections import deque
from PyQt6.QtGui import QPainter


class HistoryManager:
    """Manages undo/redo history using the Command Pattern"""
    
    def __init__(self, limit: int = 20):
        """
        Initialize history manager
        
        Args:
            limit: Maximum number of undo states (default 20)
                Older states are automatically removed to save memory
        """
        self.limit = limit
        self.undo_stack = deque(maxlen=limit)  # deque = double-ended queue (fast!)
        self.redo_stack = deque(maxlen=limit)
    
    def save_state(self, layer_index: int, image):
        
        snapshot = image.copy()  # IMPORTANT: Make a copy!
        self.undo_stack.append((layer_index, snapshot))
        self.redo_stack.clear()  # New action = can't redo old futures!
    
    def undo(self, layers):
        """
        Undo last action
        
        Args:
            layers: List of Layer objects
            
        Returns:
            int: Index of modified layer, or None if nothing to undo
        """
        if not self.undo_stack:
            return None  # Nothing to undo
        
        layer_index, old_image = self.undo_stack.pop()
        
        if layer_index < len(layers):
            current_layer = layers[layer_index]
            
            # Save current state to redo stack
            self.redo_stack.append((layer_index, current_layer.image.copy()))
            
            # Restore old state
            painter = QPainter(current_layer.image)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.drawImage(0, 0, old_image)
            painter.end()
            
            return layer_index
        
        return None
    
    def redo(self, layers):
        """
        Redo last undone action
        
        Args:
            layers: List of Layer objects
            
        Returns:
            int: Index of modified layer, or None if nothing to redo
        """
        if not self.redo_stack:
            return None  # Nothing to redo
        
        layer_index, new_image = self.redo_stack.pop()
        
        if layer_index < len(layers):
            current_layer = layers[layer_index]
            
            # Save current state to undo stack
            self.undo_stack.append((layer_index, current_layer.image.copy()))
            
            # Apply new state
            painter = QPainter(current_layer.image)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.drawImage(0, 0, new_image)
            painter.end()
            
            return layer_index
        
        return None
    
    def can_undo(self) -> bool:
        """Check if undo is available"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available"""
        return len(self.redo_stack) > 0
    
    def get_stats(self) -> dict:
        """
        Get statistics about history usage
        
        Returns:
            dict: Statistics including undo/redo counts and memory usage
        """
        return {
            'undo_count': len(self.undo_stack),
            'redo_count': len(self.redo_stack),
            'limit': self.limit,
            'undo_full': len(self.undo_stack) >= self.limit
        }
