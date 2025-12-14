from PyQt6.QtCore import QObject

class BaseTool(QObject):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def mouse_press(self, event, pos): pass
    def mouse_move(self, event, pos): pass
    def mouse_release(self, event, pos): pass
    def key_press(self, event): pass
    
    # Optional: Tools can have their own cursor
    def get_cursor(self): return None