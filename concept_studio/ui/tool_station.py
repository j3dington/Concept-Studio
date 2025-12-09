"""
Tool Station - Floating Tool Panel
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QPushButton, QSlider, 
                            QColorDialog, QMenu, QLabel, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor
from logic.project import ProjectManager


class ToolStation(QFrame):
    def __init__(self, canvas_ref, parent=None):
        super().__init__(parent)
        self.canvas = canvas_ref
        self.setObjectName("FloatingStation")
        layout = QVBoxLayout(self)
        layout.setSpacing(12) 
        layout.setContentsMargins(10, 20, 10, 20)
        
        self.btn_file = QPushButton("☰") 
        self.btn_file.setFixedSize(40, 40)
        self.btn_file.clicked.connect(self.show_file_menu)
        layout.addWidget(self.btn_file)
        self.add_divider(layout)
        
        self.btn_brush = self.create_tool_btn("🖌️", True, "Brush (B)")
        self.btn_brush.clicked.connect(lambda: self.set_tool("brush"))
        layout.addWidget(self.btn_brush)
        
        self.btn_eraser = self.create_tool_btn("🧼", False, "Eraser (E)")
        self.btn_eraser.clicked.connect(lambda: self.set_tool("eraser"))
        
        self.btn_move = self.create_tool_btn("✋", False, "Move/Rotate/Scale (V)")
        self.btn_move.clicked.connect(lambda: self.set_tool("move"))
        layout.addWidget(self.btn_move)
        
        self.btn_lasso = self.create_tool_btn("➰", False, "Free Lasso (L)")
        self.btn_lasso.clicked.connect(lambda: self.set_tool("lasso"))
        layout.addWidget(self.btn_lasso)
        
        self.btn_poly = self.create_tool_btn("📐", False, "Poly Lasso (P)")
        self.btn_poly.clicked.connect(lambda: self.set_tool("poly_lasso"))
        layout.addWidget(self.btn_poly)
        
        self.btn_add = QPushButton("➕")
        self.btn_add.setFixedSize(40, 40)
        self.btn_add.clicked.connect(self.show_add_menu)
        layout.addWidget(self.btn_add)
        
        self.add_divider(layout)
        
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(36, 36)
        self.btn_color.setStyleSheet(f"background-color: {self.canvas.brush_color.name()}; border-radius: 18px; border: 2px solid rgba(255,255,255,0.2);")
        self.btn_color.clicked.connect(self.pick_color)
        layout.addWidget(self.btn_color, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addWidget(QLabel("SIZE"), 0, Qt.AlignmentFlag.AlignHCenter)
        self.slider_size = QSlider(Qt.Orientation.Vertical)
        self.slider_size.setRange(1, 100)
        self.slider_size.setValue(5)
        self.slider_size.setFixedHeight(120)
        self.slider_size.valueChanged.connect(lambda v: setattr(self.canvas, 'brush_size', v))
        layout.addWidget(self.slider_size, 0, Qt.AlignmentFlag.AlignHCenter)
        
        layout.addStretch()
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30); shadow.setColor(QColor(0,0,0,80)); shadow.setOffset(0,8)
        self.setGraphicsEffect(shadow)

    def add_divider(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: rgba(255,255,255,0.1);")
        line.setFixedWidth(30)
        layout.addWidget(line, 0, Qt.AlignmentFlag.AlignHCenter)

    def create_tool_btn(self, icon, checked, tooltip): 
        btn = QPushButton(icon)
        btn.setCheckable(True)
        btn.setChecked(checked)
        btn.setFixedSize(40, 40)
        btn.setToolTip(tooltip)
        return btn
    
    def set_tool(self, tool_name):
        # Auto-Commit if leaving ANY transform tool
        transform_tools = ["move", "rotate", "scale"]
        if self.canvas.current_tool in transform_tools and tool_name not in transform_tools: 
            self.canvas.commit_transform()

        self.canvas.current_tool = tool_name
        self.canvas.is_eraser = (tool_name == "eraser")
        
        # Visual Button Updates
        self.btn_brush.setChecked(tool_name == "brush")
        self.btn_eraser.setChecked(tool_name == "eraser")
        # Keep "Move" button lit up for all transform modes so the user knows they are transforming
        self.btn_move.setChecked(tool_name in transform_tools)
        self.btn_lasso.setChecked(tool_name == "lasso")
        self.btn_poly.setChecked(tool_name == "poly_lasso")
        
        # Cursors
        if tool_name == "move": self.canvas.setCursor(Qt.CursorShape.SizeAllCursor)
        elif tool_name == "rotate": self.canvas.setCursor(Qt.CursorShape.SizeHorCursor) # Left/Right arrows
        elif tool_name == "scale": self.canvas.setCursor(Qt.CursorShape.SizeBDiagCursor) # Diagonal arrows
        elif "lasso" in tool_name: self.canvas.setCursor(Qt.CursorShape.CrossCursor)
        elif tool_name in ["brush", "eraser"]: self.canvas.setCursor(Qt.CursorShape.BlankCursor)
        else: self.canvas.setCursor(Qt.CursorShape.ArrowCursor)

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.canvas.brush_color = color
            self.btn_color.setStyleSheet(f"background-color: {color.name()}; border-radius: 18px; border: 2px solid rgba(255,255,255,0.2);")

    def show_add_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2d2d2d; color: #fff; border: 1px solid #3d3d3d; }")
        menu.addAction("👆 Smudge Tool")
        menu.addAction("🪣 Fill Bucket")
        menu.exec(self.btn_add.mapToGlobal(QPoint(50, 0)))

    def show_file_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2d2d2d; color: #fff; border: 1px solid #3d3d3d; }")
        action_save = menu.addAction("💾 Save Project (.csp)")
        action_load = menu.addAction("📂 Open Project")
        menu.addSeparator()
        action_import = menu.addAction("⬇️ Import Image")
        menu.addSeparator()
        action_export = menu.addAction("🖼️ Export PNG")
        action = menu.exec(self.btn_file.mapToGlobal(QPoint(50, 0)))
        
        if action == action_save: ProjectManager.save_project(self, self.canvas.layers, self.canvas.canvas_width, self.canvas.canvas_height)
        elif action == action_load: 
            ProjectManager.load_project(self, self.canvas)
            if hasattr(self.parent(), 'layer_panel'): 
                self.parent().layer_panel.refresh_list()
        elif action == action_import: 
            self.canvas.import_image_layer()
            if hasattr(self.parent(), 'layer_panel'): 
                self.parent().layer_panel.refresh_list()
        elif action == action_export: ProjectManager.export_image(self, self.canvas)
