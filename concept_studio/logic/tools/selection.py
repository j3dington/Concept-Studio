from PyQt6.QtGui import QPainterPath, QPolygonF
from PyQt6.QtCore import Qt, QPointF
from .base import BaseTool

class LassoTool(BaseTool):
    def __init__(self, canvas, poly_mode=False):
        super().__init__(canvas)
        self.poly_mode = poly_mode

    def mouse_press(self, event, pos):
        if not self.poly_mode:
            # === Freehand: Reset and start new === #
            self.canvas.is_selecting = True
            self.canvas.selection_path = QPainterPath()
            self.canvas.lasso_points = [pos]
        else:
            # === Poly: Append point === #
            if not self.canvas.lasso_points:
                self.canvas.selection_path = QPainterPath()
            self.canvas.lasso_points.append(pos)
            self.canvas.update()

    def mouse_move(self, event, pos):
        if not self.poly_mode and self.canvas.is_selecting:
            self.canvas.lasso_points.append(pos)
            self.canvas.update()

    def mouse_release(self, event, pos):
        if not self.poly_mode:
            self.canvas.is_selecting = False
            self.close_selection()

    def key_press(self, event):
        if self.poly_mode and event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter]:
            self.close_selection()

    def close_selection(self):
        if len(self.canvas.lasso_points) > 2:
            self.canvas.selection_path.addPolygon(QPolygonF([QPointF(p) for p in self.canvas.lasso_points]))
            self.canvas.selection_path.closeSubpath()
        self.canvas.lasso_points = []
        self.canvas.update()