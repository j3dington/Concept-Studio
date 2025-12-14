from PyQt6.QtCore import Qt, QPointF
from .base import BaseTool

class TransformTool(BaseTool):
    def __init__(self, canvas, mode="move"):
        super().__init__(canvas)
        self.mode = mode # "move", "rotate", "scale"
        self.start_pos = None

    def mouse_press(self, event, pos):
        # === Auto-Lift Logic === #
        if not self.canvas.selection_path.isEmpty():
            layer = self.canvas.layers[self.canvas.active_layer_index]
            if not layer.is_floating:
                if self.canvas.lift_selection_to_layer():
                    pass # Lifted successfully

        self.start_pos = event.pos() # Screen coordinates for deltas

    def mouse_move(self, event, pos):
        if not self.start_pos: return
        
        delta = event.pos() - self.start_pos
        if not (0 <= self.canvas.active_layer_index < len(self.canvas.layers)): return
        layer = self.canvas.layers[self.canvas.active_layer_index]

        if self.mode == "rotate" or (self.mode == "move" and event.buttons() & Qt.MouseButton.RightButton):
            layer.rotation += delta.x() * 0.5
        elif self.mode == "scale" or (self.mode == "move" and event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            change = delta.x() * 0.01
            layer.scale_x += change
            layer.scale_y += change
        else:
            layer.x += delta.x() / self.canvas.scale_factor
            layer.y += delta.y() / self.canvas.scale_factor

        self.start_pos = event.pos()
        self.canvas.update()
        
    def mouse_release(self, event, pos):
        self.start_pos = None

    def key_press(self, event):
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.canvas.commit_transform()
            # Optional: Switch tool back via parent logic if needed