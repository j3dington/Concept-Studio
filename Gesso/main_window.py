from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QToolButton, QFrame, QSizePolicy, QSpacerItem, QPushButton,
                            QSlider, QLabel, QColorDialog, QFileDialog, QMessageBox, QMenu)
from PyQt6.QtGui import QAction, QActionGroup, QResizeEvent, QColor, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSize, QPoint, QRect

# --- LOCAL IMPORTS ---
from canvas import Canvas
from enums import ToolType
from layer_panel import LayerPanel
from draggable import DraggableFrame
from styles import get_stylesheet
from assets import get_qicon, get_custom_cursor, get_available_brushes, load_custom_fonts
from brush_settings import BrushSettingsPanel
from diagnostics import DiagnosticsPanel

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gesso")
        self.setWindowIcon(get_qicon("logo"))
        self.resize(1400, 900)
        
        # Load Fonts and Cursors
        self.ui_font_name = load_custom_fonts(preferred_font="DM SANS")
        self.custom_arrow = get_custom_cursor("cursor_arrow", color="#2D2D2D", scale=0.4, rotation=15, hotspot=(0, 0))
        self.custom_hand = get_custom_cursor("cursor_hand_pointing", color="#2D2D2D", scale=0.4, hotspot=(0, 0))
        self.setCursor(self.custom_arrow)
        
        self.panels_positioned = False 
        
        # 1. THE CONTAINER
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        # 2. THE CANVAS
        self.canvas = Canvas()
        self.canvas.setParent(self.container)
        
        # 3. THE BAG (Left Panel)
        self.bag_frame = DraggableFrame(self.container)
        self.bag_frame.setObjectName("TheBag")
        
        # 4. DIAGNOSTICS (Initialize before populating the Bag)
        self.diagnostics = DiagnosticsPanel(self.canvas)
        self.diagnostics.setParent(self)
        self.diagnostics.hide()
        
        # FIX: We only call this ONCE now
        self.setup_the_bag_content()
        
        # 5. LAYER PANEL
        self.layer_panel = LayerPanel(self.canvas) 
        self.layer_panel.setParent(self.container)
        self.layer_panel.setObjectName("LayerPanel")
        
        # 6. BRUSH STUDIO
        self.brush_studio = BrushSettingsPanel(self.canvas)
        self.brush_studio.setParent(self.container)
        self.brush_studio.hide()
        
        # 7. SIGNALS & MENUS
        self.canvas.color_changed.connect(self.brush_studio.color_picker.set_color)
        self.diagnostics.visibility_changed.connect(self.sync_diag_ui)
        self.canvas.tool_changed.connect(self.update_bag_ui)
        
        self.setup_menus()
        self.setup_shortcuts()
    
    def setup_the_bag_content(self):
        """Builds the left sidebar."""
        layout = QVBoxLayout(self.bag_frame)
        layout.setContentsMargins(14, 25, 14, 25) 
        layout.setSpacing(12) 
        
        self.tool_group = QActionGroup(self)
        
        # --- TOP: BRUSH STUDIO TOGGLE ---
        self.btn_studio = QToolButton()
        self.btn_studio.setIcon(get_qicon("sliders"))
        self.btn_studio.setFixedSize(40, 40)
        self.btn_studio.setCheckable(True)
        self.btn_studio.clicked.connect(self.toggle_brush_studio)
        self.btn_studio.setCursor(self.custom_hand)
        
        self.btn_diag = QPushButton("📊")
        self.btn_diag.setFixedSize(40, 40)
        self.btn_diag.setToolTip("Toggle System Diagnostics (D)")
        self.btn_diag.setCheckable(True)
        self.btn_diag.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 20px; /* Circular button */
                font-size: 18px;
            }
            QPushButton:checked {
                background-color: #BA4A00; /* ConceptStudio Orange */
                color: white;
            }
        """)
        
        self.btn_diag.clicked.connect(self.toggle_diagnostics)
        self.layout.addWidget(self.btn_diag)
        
        # Center it
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(self.btn_studio)
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Divider
        line_top = QFrame()
        line_top.setFrameShape(QFrame.Shape.HLine)
        line_top.setStyleSheet("color: #E0DED7;") 
        layout.addWidget(line_top)
        
        def add_btn(icon_name, shortcut, ttype):
            action = QAction(self)
            action.setCheckable(True)
            if shortcut: action.setShortcut(shortcut)
            action.setIcon(get_qicon(icon_name))
            action.triggered.connect(lambda: self.canvas.set_tool(ttype))
            self.tool_group.addAction(action)
            
            btn = QToolButton()
            btn.setDefaultAction(action)
            btn.setCursor(self.custom_hand)
            btn.setIconSize(QSize(22, 22)) 
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            layout.addWidget(btn)
            return action

        # --- TOOLS ---
        self.act_move = add_btn("move", "V", ToolType.MOVE)
        self.act_marq = add_btn("marquee", "M", ToolType.MARQUEE)
        self.act_lasso = add_btn("lasso", "L", ToolType.LASSO)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #E0DED7;") 
        layout.addWidget(line)
        
        self.act_brush = add_btn("brush", "B", ToolType.BRUSH)
        self.act_erase = add_btn("eraser", "E", ToolType.ERASER)
        self.act_fill  = add_btn("fill", "G", ToolType.FILL)
        self.act_eye   = add_btn("eyedropper", "I", ToolType.EYEDROPPER)
        
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # --- PROPERTIES ---
        
        # Color Chip
        self.btn_color = QToolButton()
        self.btn_color.setFixedSize(30, 30) 
        self.btn_color.setStyleSheet(f"background-color: {self.canvas.brush_color.name()}; border-radius: 15px; border: 1px solid #ccc;")
        self.btn_color.clicked.connect(self.open_color_picker)
        self.btn_color.setCursor(self.custom_hand)
        
        color_layout = QHBoxLayout()
        color_layout.addStretch()
        color_layout.addWidget(self.btn_color)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # BRUSH SHAPE SELECTOR
        self.btn_brush_tip = QToolButton()
        self.btn_brush_tip.setText("BRUSH") 
        self.btn_brush_tip.setToolTip("Change Brush Tip")
        self.btn_brush_tip.setCursor(self.custom_hand)
        self.btn_brush_tip.setStyleSheet("""
            QToolButton {
                background-color: #E0E0E0;
                color: #333;
                border-radius: 10px;
                padding: 4px;
                font-size: 8pt;
                font-weight: bold;
            }
            QToolButton:hover { background-color: #D6D6D6; }
            QToolButton::menu-indicator { image: none; }
        """)
        self.btn_brush_tip.setFixedHeight(24)
        self.btn_brush_tip.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.update_brush_menu()
        layout.addWidget(self.btn_brush_tip)

        # SLIDERS (Note: We now capture the slider object!)
        container_size, self.slider_size = self.create_slider("SIZE", 1, 1000, 20, self.canvas.set_brush_size)
        layout.addWidget(container_size)
        
        container_op, self.slider_opacity = self.create_slider("OPACITY", 1, 100, 100, self.canvas.set_brush_opacity)
        layout.addWidget(container_op)
        
        # --- SYSTEM BUTTONS ---
        layout.addSpacing(10)
        sys_container = QWidget()
        sys_layout = QHBoxLayout(sys_container)
        sys_layout.setContentsMargins(0, 0, 0, 0)
        sys_layout.setSpacing(6) 
        
        sys_layout.addStretch() 
        
        def make_sys_btn(icon, func):
            b = QToolButton()
            b.setIcon(get_qicon(icon))
            b.setFixedSize(28, 28)
            b.setIconSize(QSize(16, 16))
            b.clicked.connect(func)
            b.setCursor(self.custom_hand)
            return b

        btn_save = make_sys_btn("save", self.save_file)
        btn_load = make_sys_btn("folder", self.load_file)
        btn_theme = make_sys_btn("palette", self.pick_ui_color)
        
        sys_layout.addWidget(btn_save)
        sys_layout.addWidget(btn_load)
        sys_layout.addWidget(btn_theme)
        
        sys_layout.addStretch() 
        layout.addWidget(sys_container)
        
        self.act_brush.setChecked(True)
        
        
    def toggle_brush_studio(self, checked):
        if checked:
            self.brush_studio.show()
            self.brush_studio.raise_()
            cx = self.width() // 2 - 125
            cy = self.height() // 2 - 200
            self.brush_studio.move(cx, cy)
        else:
            self.brush_studio.hide()

    def create_slider(self, label_text, min_val, max_val, default_val, callback):
        """Returns (ContainerWidget, SliderObject)."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(4)
        
        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.valueChanged.connect(callback)
        layout.addWidget(slider)
        slider.setCursor(self.custom_hand)
        
        return container, slider
    
    def decrease_brush_size(self):
        """Safely lowers the slider value."""
        current = self.slider_size.value()
        self.slider_size.setValue(max(1, current - 10))

    def increase_brush_size(self):
        """Safely raises the slider value."""
        current = self.slider_size.value()
        self.slider_size.setValue(min(1000, current + 10))

    def update_brush_menu(self):
        menu = QMenu(self)
        
        action_soft = QAction("Soft Round", self)
        action_soft.triggered.connect(lambda: self.set_brush_shape("Soft"))
        menu.addAction(action_soft)
        
        menu.addSeparator()
        
        files = get_available_brushes()
        if not files:
            dummy = QAction("(No brushes found)", self)
            dummy.setEnabled(False)
            menu.addAction(dummy)
        else:
            for f in files:
                self.add_brush_action(menu, f)
                
        self.btn_brush_tip.setMenu(menu)

    def add_brush_action(self, menu, filename):
        display_name = filename.split('.')[0].replace('_', ' ').title()
        action = QAction(display_name, self)
        action.triggered.connect(lambda: self.set_brush_shape(filename))
        menu.addAction(action)

    def set_brush_shape(self, shape_name):
        self.canvas.set_brush_shape(shape_name)
        if shape_name == "Soft":
            self.btn_brush_tip.setText("SOFT")
        else:
            short_name = shape_name.split('.')[0][:5].upper()
            self.btn_brush_tip.setText(short_name)

    def open_color_picker(self):
        color = QColorDialog.getColor(self.canvas.brush_color, self, "Select Color")
        if color.isValid():
            self.canvas.set_brush_color(color)
            self.btn_color.setStyleSheet(
                f"background-color: {color.name()}; border-radius: 15px; border: 1px solid #ccc;"
            )

    def apply_theme(self, hex_color):
        css = get_stylesheet(
            base_color=hex_color, 
            header_font=self.header_font, 
            body_font=self.body_font
        )
        self.setStyleSheet(css)

    def pick_ui_color(self):
        c = QColorDialog.getColor(QColor("#FFFFFF"), self, "Pick UI Base Color")
        if c.isValid():
            self.apply_theme(c.name())

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Artwork", "", 
            "Concept Project (*.concept);;PNG Image (*.png)"
        )
        if path:
            if path.endswith(".concept"):
                self.canvas.save_project(path)
            else:
                self.canvas.export_image(path)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Artwork", "",
            "Concept Project (*.concept)"
        )
        if path:
            success = self.canvas.load_project(path)
            if success:
                self.layer_panel.refresh_layers()

    def update_bag_ui(self, tool_type):
        if tool_type == ToolType.BRUSH: self.act_brush.setChecked(True)
        elif tool_type == ToolType.EYEDROPPER: self.act_eye.setChecked(True)
        elif tool_type == ToolType.MOVE: self.act_move.setChecked(True)
        elif tool_type == ToolType.MARQUEE: self.act_marq.setChecked(True)
        elif tool_type == ToolType.ERASER: self.act_erase.setChecked(True)
        elif tool_type == ToolType.FILL: self.act_fill.setChecked(True)
        elif tool_type == ToolType.LASSO: self.act_lasso.setChecked(True)