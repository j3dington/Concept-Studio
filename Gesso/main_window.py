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
        # 1. SYSTEM INITIALIZATION (The POST Sequence)
        # We define the basic window properties first.
        self.setWindowTitle("Gesso")
        self.setWindowIcon(get_qicon("logo"))
        self.resize(1400, 900)
        
        # Load custom resources (Fonts & Cursors)
        self.ui_font_name = load_custom_fonts(preferred_font="DM SANS")
        self.custom_arrow = get_custom_cursor("cursor_arrow", color="#2D2D2D", scale=0.4, rotation=15, hotspot=(0, 0))
        self.custom_hand = get_custom_cursor("cursor_hand_pointing", color="#2D2D2D", scale=0.4, hotspot=(0, 0))
        self.setCursor(self.custom_arrow)
        
        self.panels_positioned = False 
        
        # 2. CORE COMPONENTS
        # The 'container' is our Motherboard; everything else plugs into it.
        self.container = QWidget()
        self.setCentralWidget(self.container)
        
        self.canvas = Canvas()
        self.canvas.setParent(self.container)
        
        # 3. INTERFACE CONTAINERS (Building the Shelves)
        self.bag_frame = DraggableFrame(self.container)
        self.bag_frame.setObjectName("TheBag")
        
        # 4. DIAGNOSTICS PANEL (Initialize early so other parts can talk to it)
        self.diagnostics = DiagnosticsPanel(self.canvas)
        self.diagnostics.setParent(self)
        self.diagnostics.hide()
        
        # 5. CONTENT POPULATION (Executing the Setup)
        # This builds the buttons inside the Bag. We call it exactly ONCE.
        self.setup_the_bag_content()
        
        # 6. SECONDARY PANELS
        self.layer_panel = LayerPanel(self.canvas) 
        self.layer_panel.setParent(self.container)
        self.layer_panel.setObjectName("LayerPanel")
        
        self.brush_studio = BrushSettingsPanel(self.canvas)
        self.brush_studio.setParent(self.container)
        self.brush_studio.hide()
        
        # 7. THEME & APPEARANCE
        self.header_font = "Lora"   
        self.body_font = "DM Sans"
        self.apply_theme("#FFFFFF")
        
        # 8. COMMUNICATION (Signals & Slots)
        # This connects the 'Brain' (Canvas) to the 'Displays' (Panels)
        self.canvas.color_changed.connect(self.brush_studio.color_picker.set_color)
        self.diagnostics.visibility_changed.connect(self.sync_diag_ui)
        self.canvas.tool_changed.connect(self.update_bag_ui)
        
        # 9. INPUT MAPPING
        self.setup_menus()
        self.setup_shortcuts()

    # --- UI BUILDER METHODS ---

    def setup_the_bag_content(self):
        """Creates the internal layout and tools for the Bag sidebar."""
        # 'layout' is a local variable used only for building. 
        # Using self.bag_frame as the parent ensures correct nesting.
        layout = QVBoxLayout(self.bag_frame)
        layout.setContentsMargins(14, 25, 14, 25) 
        layout.setSpacing(12) 
        
        self.tool_group = QActionGroup(self)
        
        # --- TOP UTILITY ROW ---
        # Brush Studio Toggle
        self.btn_studio = QToolButton()
        self.btn_studio.setIcon(get_qicon("sliders"))
        self.btn_studio.setFixedSize(40, 40)
        self.btn_studio.setCheckable(True)
        self.btn_studio.clicked.connect(self.toggle_brush_studio)
        self.btn_studio.setCursor(self.custom_hand)
        
        # Diagnostics Toggle
        self.btn_diag = QPushButton("📊")
        self.btn_diag.setFixedSize(40, 40)
        self.btn_diag.setToolTip("Toggle System Diagnostics (D)")
        self.btn_diag.setCheckable(True)
        self.btn_diag.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:checked {
                background-color: #BA4A00;
                color: white;
            }
        """)
        self.btn_diag.clicked.connect(self.toggle_diagnostics)
        
        # Grouping Studio and Diagnostics at the top
        top_btn_layout = QHBoxLayout()
        top_btn_layout.addStretch()
        top_btn_layout.addWidget(self.btn_studio)
        top_btn_layout.addSpacing(8)
        top_btn_layout.addWidget(self.btn_diag)
        top_btn_layout.addStretch()
        layout.addLayout(top_btn_layout)
        
        # Aesthetic Divider
        line_top = QFrame()
        line_top.setFrameShape(QFrame.Shape.HLine)
        line_top.setStyleSheet("color: #E0DED7;") 
        layout.addWidget(line_top)

        # Helper function for adding tools to the sidebar
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

        # --- ART TOOLS ---
        self.act_move = add_btn("move", "V", ToolType.MOVE)
        self.act_marq = add_btn("marquee", "M", ToolType.MARQUEE)
        self.act_lasso = add_btn("lasso", "L", ToolType.LASSO)
        
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("color: #E0DED7;") 
        layout.addWidget(divider)
        
        self.act_brush = add_btn("brush", "B", ToolType.BRUSH)
        self.act_erase = add_btn("eraser", "E", ToolType.ERASER)
        self.act_fill  = add_btn("fill", "G", ToolType.FILL)
        self.act_eye   = add_btn("eyedropper", "I", ToolType.EYEDROPPER)
        
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # --- BRUSH PROPERTIES ---
        # Current Color Chip
        self.btn_color = QToolButton()
        self.btn_color.setFixedSize(30, 30) 
        self.btn_color.setStyleSheet(f"background-color: {self.canvas.brush_color.name()}; border-radius: 15px; border: 1px solid #ccc;")
        self.btn_color.clicked.connect(self.open_color_picker)
        self.btn_color.setCursor(self.custom_hand)
        
        color_row = QHBoxLayout()
        color_row.addStretch()
        color_row.addWidget(self.btn_color)
        color_row.addStretch()
        layout.addLayout(color_row)
        
        tip_row = QHBoxLayout()
        tip_row.setSpacing(8)
        self.brush_preview_label = QLabel()
        self.brush_preview_label.setFixedSize(24, 24)
        self.brush_preview_label.setStyleSheet("background-color: #F0F0F0; border-radius: 5px; border: 1px solid #D6D6D6;")
        self.brush_preview_label.setScaledContents(True) # Ensures the image fits the 24x24 box
        
        self.btn_brush_tip = QToolButton()
        self.btn_brush_tip.setText("BRUSH") 
        self.btn_brush_tip.setFixedHeight(24)
        self.btn_brush_tip.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.btn_brush_tip.setCursor(self.custom_hand)
        self.btn_brush_tip.setStyleSheet("""
            QToolButton { background-color: #E0E0E0; color: #333; border-radius: 10px; font-weight: bold; font-size: 8pt; }
            QToolButton::menu-indicator { image: none; }
        """)
        self.update_brush_menu()
        
        tip_row.addWidget(self.brush_preview_label)
        tip_row.addWidget(self.btn_brush_tip)
        layout.addLayout(tip_row)
        
        # Size and Opacity Sliders
        container_size, self.slider_size = self.create_slider("SIZE", 1, 1000, 20, self.canvas.set_brush_size)
        layout.addWidget(container_size)
        
        container_op, self.slider_opacity = self.create_slider("OPACITY", 1, 100, 100, self.canvas.set_brush_opacity)
        layout.addWidget(container_op)

        # Default Tool Selection
        self.act_brush.setChecked(True)

    # --- EVENT HANDLERS & HELPERS ---

    def setup_shortcuts(self):
        self.shortcut_shrink = QShortcut(QKeySequence("["), self)
        self.shortcut_shrink.activated.connect(self.decrease_brush_size)
        
        self.shortcut_grow = QShortcut(QKeySequence("]"), self)
        self.shortcut_grow.activated.connect(self.increase_brush_size)

    def sync_diag_ui(self, is_open):
        """Keeps all UI elements in sync with the DiagnosticsPanel visibility."""
        self.btn_diag.setChecked(is_open)
        if hasattr(self, 'diag_action'):
            self.diag_action.setChecked(is_open)

    def toggle_diagnostics(self):
        """Unified toggle logic for Hotkey, Menu, and Bag Button."""
        is_visible = self.diagnostics.isVisible()
        if is_visible:
            self.diagnostics.hide()
        else:
            self.diagnostics.show()
            self.diagnostics.move(20, self.height() - 120)
            
    def update_brush_menu(self):
        # 1. Create the Menu object
        print("LOG: update_brush_menu is running!")
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #FFFFFF; border: 1px solid #CCCCCC; }")

        action_soft = QAction("Soft Round", self)
        action_soft.triggered.connect(lambda: self.set_brush_shape("Soft"))
        menu.addAction(action_soft)
        
        menu.addSeparator() 
        brushes = get_available_brushes() 
        
        if brushes:
            for b in brushes:
                display_name = b.split('.')[0].replace('_', ' ').title()
                action = QAction(display_name, self)
                
                action.triggered.connect(lambda checked, f=b: self.set_brush_shape(f))
                
                menu.addAction(action)
        
        self.btn_brush_tip.setMenu(menu)

    def set_brush_shape(self, shape_name):
        """Updates the Canvas and the Preview UI."""
        self.canvas.set_brush_shape(shape_name)
        
        label = "SOFT" if shape_name == "Soft" else shape_name.split('.')[0][:5].upper()
        self.btn_brush_tip.setText(label)
        
        icon = get_qicon("brush") if shape_name == "Soft" else get_qicon(shape_name)
        self.brush_preview_label.setPixmap(icon.pixmap(24, 24))

    def setup_menus(self):
        menubar = self.menuBar()
        view_menu = menubar.addMenu("&View")
        
        self.diag_action = QAction("System Diagnostics", self)
        self.diag_action.setCheckable(True)
        self.diag_action.setShortcut("D")
        self.diag_action.triggered.connect(self.toggle_diagnostics)
        view_menu.addAction(self.diag_action)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_D:
            self.toggle_diagnostics()
        elif event.key() == Qt.Key.Key_Z:
            self.canvas.keyPressEvent(event)
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Standard window resize handler to keep 'Islands' in place."""
        w, h = self.container.width(), self.container.height()
        self.canvas.setGeometry(0, 0, w, h)
        
        if not self.panels_positioned:
            self.bag_frame.setGeometry(20, 30, 125, h - 60)
            self.layer_panel.setGeometry(w - 260, 30, 240, h - 60)
            self.panels_positioned = True
        super().resizeEvent(event)

    def create_slider(self, label_text, min_val, max_val, default_val, callback):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        lbl = QLabel(label_text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.setValue(default_val)
        slider.valueChanged.connect(callback)
        layout.addWidget(slider)
        return container, slider

    def toggle_brush_studio(self, checked):
        if checked:
            self.brush_studio.show()
            self.brush_studio.raise_()
            self.brush_studio.move(self.width()//2 - 125, self.height()//2 - 200)
        else:
            self.brush_studio.hide()

    def decrease_brush_size(self):
        self.slider_size.setValue(max(1, self.slider_size.value() - 10))

    def increase_brush_size(self):
        self.slider_size.setValue(min(1000, self.slider_size.value() + 10))

    def open_color_picker(self):
        color = QColorDialog.getColor(self.canvas.brush_color, self, "Select Color")
        if color.isValid():
            self.canvas.set_brush_color(color)
            self.btn_color.setStyleSheet(f"background-color: {color.name()}; border-radius: 15px; border: 1px solid #ccc;")

    def apply_theme(self, hex_color):
        css = get_stylesheet(base_color=hex_color, header_font=self.header_font, body_font=self.body_font)
        self.setStyleSheet(css)

    def pick_ui_color(self):
        c = QColorDialog.getColor(QColor("#FFFFFF"), self, "Pick UI Base Color")
        if c.isValid(): self.apply_theme(c.name())

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Artwork", "", "Concept Project (*.concept);;PNG Image (*.png)")
        if path:
            if path.endswith(".concept"): self.canvas.save_project(path)
            else: self.canvas.export_image(path)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Artwork", "", "Concept Project (*.concept)")
        if path:
            if self.canvas.load_project(path): self.layer_panel.refresh_layers()

    def update_bag_ui(self, tool_type):
        if tool_type == ToolType.BRUSH: self.act_brush.setChecked(True)
        elif tool_type == ToolType.EYEDROPPER: self.act_eye.setChecked(True)
        elif tool_type == ToolType.MOVE: self.act_move.setChecked(True)
        elif tool_type == ToolType.MARQUEE: self.act_marq.setChecked(True)
        elif tool_type == ToolType.ERASER: self.act_erase.setChecked(True)
        elif tool_type == ToolType.FILL: self.act_fill.setChecked(True)
        elif tool_type == ToolType.LASSO: self.act_lasso.setChecked(True)