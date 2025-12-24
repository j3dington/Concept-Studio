from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QToolButton, QFrame, QSizePolicy, QSpacerItem, QPushButton,
                            QSlider, QLabel, QColorDialog, QFileDialog, QMessageBox, QMenu,
                            QDialog, QSpinBox, QFormLayout, QDialogButtonBox, QMenuBar)
from PyQt6.QtGui import QAction, QActionGroup, QResizeEvent, QColor, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSize, QPoint, QRect

# --- LOCAL IMPORTS ---
from canvas import Canvas
from enums import ToolType
from layer_panel import LayerPanel
from draggable import DraggableFrame
from styles import get_stylesheet
from assets import get_qicon, get_custom_cursor, get_available_brushes, load_custom_fonts
from brush_settings import BrushSettingsPanel, BrushSettings
from diagnostics import DiagnosticsPanel
from reference_board_window import ReferenceBoardWindow
from drawing_engine import DrawingEngine

class NewCanvasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NEW PROJECT")
        self.setFixedSize(300, 200)
        
        self.setStyleSheet("""
            QDialog { background-color: #FFFFFF; border: 2px solid #FF6000; border-radius: 10px; }
            QLabel { font-weight: bold; color: #757575; }
            QSpinBox { padding: 5px; border: 1px solid #E0E0E0; border-radius: 4px; }
        """)

        layout = QFormLayout(self)
        
        # Inputs for Width/Height
        self.width_input = QSpinBox()
        self.width_input.setRange(100, 8000)
        self.width_input.setValue(1920) # Default to Full HD
        
        self.height_input = QSpinBox()
        self.height_input.setRange(100, 8000)
        self.height_input.setValue(1080)

        layout.addRow("WIDTH (PX)", self.width_input)
        layout.addRow("HEIGHT (PX)", self.height_input)

        # OK/Cancel Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_dimensions(self):
        return self.width_input.value(), self.height_input.value()

class CustomTitleBar(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(40)
        self.parent = parent
        
        self.drag_pos = QPoint() 
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 5, 0)
        
        self.title_label = QLabel("GESSO")
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(30, 30)
        self.btn_close.clicked.connect(self.parent.close)
        layout.addWidget(self.btn_close)

    # --- THE DRAG ENGINE ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # We store the position of the click RELATIVE to the window's top-left
            self.drag_pos = event.globalPosition().toPoint() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # We move the window to the current mouse pos minus the original click offset
            self.parent.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

class MainWindow(QMainWindow):
    def __init__(self, canvas_width, canvas_height):
        super().__init__()
        # 1. THE OS FLAGS (The Handshake)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    

        # 2. THE SHELL (The Case)
        self.root_container = QFrame()
        self.root_container.setObjectName("RootFrame")
        self.setCentralWidget(self.root_container)

        # 3. THE MASTER LAYOUT
        self.main_layout = QVBoxLayout(self.root_container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 4. THE CUSTOM TITLE BAR
        self.title_bar = CustomTitleBar(self)
        self.main_layout.addWidget(self.title_bar)
        
        # 5. THE MOTHERBOARD
        self.container = QWidget()
        self.main_layout.addWidget(self.container) # This puts it UNDER the title bar

        # ==== NOW CONTINUE WITH YOUR EXISTING SETUP ====
        self.setWindowTitle("Gesso")
        self.setWindowIcon(get_qicon("logo"))
        self.resize(1400, 900)
        
        # Load custom resources (Fonts & Cursors)
        self.ui_font_name = load_custom_fonts(preferred_font="DM SANS")
        self.custom_arrow = get_custom_cursor("cursor_arrow", color="#2D2D2D", scale=0.4, rotation=15, hotspot=(0, 0))
        self.setCursor(self.custom_arrow)
        self.custom_hand = get_custom_cursor("cursor_hand_pointing", color="#2D2D2D", scale=0.4, hotspot=(0, 0))
                
        self.panels_positioned = False 
        
        # 2. CORE COMPONENTS
        self.drawing_engine = DrawingEngine()
        self.canvas = Canvas(canvas_width, canvas_height)
        self.canvas.engine = self.drawing_engine
        self.canvas.setParent(self.container)
        
        # 3. INTERFACE CONTAINERS (Building the Shelves)
        self.bag_frame = DraggableFrame(self.container)
        self.bag_frame.setObjectName("TheBag")
        
        # 4. DIAGNOSTICS PANEL (Initialize early so other parts can talk to it)
        self.diagnostics = DiagnosticsPanel(self.canvas)
        self.diagnostics.setParent(self)
        self.diagnostics.hide()
        
        self.setup_the_bag_content()
        
        # 6. SECONDARY PANELS
        self.layer_panel = LayerPanel(self.canvas) 
        self.layer_panel.setParent(self.container)
        self.layer_panel.setObjectName("LayerPanel")
        
        self.brush_studio = BrushSettingsPanel(self.canvas)
        self.brush_studio.setParent(self.container)
        self.brush_studio.hide()
        
        # 7. THEME & APPEARANCE
        self.header_font = "Inter"   
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
        self.reference_board_window = None

    def center_canvas(self):
        """Calculates the center of the screen to place the paper."""
        if hasattr(self, 'canvas'):
            # Find the middle of the app window
            win_center = self.container.rect().center()
            
            # Find the middle of the paper (at current scale)
            paper_w = self.canvas.canvas_width * self.canvas.view_scale
            paper_h = self.canvas.canvas_height * self.canvas.view_scale
            
            # Set the offset so the paper is perfectly centered
            new_x = win_center.x() - (paper_w / 2)
            new_y = win_center.y() - (paper_h / 2)
            self.canvas.view_offset = QPoint(int(new_x), int(new_y))
            self.canvas.update()

    # --- UI BUILDER METHODS ---
    
    def setup_the_bag_content(self):
        """Creates the internal layout and tools for the Bag sidebar."""
        layout = QVBoxLayout(self.bag_frame)
        layout.setContentsMargins(10, 15, 10, 15) 
        layout.setSpacing(12) 
        
        self.tool_group = QActionGroup(self)
        
        top_btn_layout = QHBoxLayout()
        top_btn_layout.setSpacing(4)
        
        # --- TOP UTILITY ROW ---
        # Brush Studio Toggle
        self.btn_studio = QToolButton()
        self.btn_studio.setIcon(get_qicon("sliders"))
        self.btn_studio.setFixedSize(36, 36)
        self.btn_studio.setCheckable(True)
        self.btn_studio.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:checked {
                background-color: #BA4A00;
                color: white;
            }
        """)
        self.btn_studio.clicked.connect(self.toggle_brush_studio)
        self.btn_studio.setCursor(self.custom_hand)
        
        # Diagnostics Toggle
        self.btn_diag = QToolButton()
        self.btn_diag.setIcon(get_qicon("gauge"))
        self.btn_diag.setFixedSize(36, 36)
        self.btn_diag.setToolTip("Toggle System Diagnostics (D)")
        self.btn_diag.setCheckable(True)
        self.btn_diag.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:checked {
                background-color: #BA4A00;
                color: white;
            }
        """)
        self.btn_diag.clicked.connect(self.toggle_diagnostics)
        self.btn_studio.setCursor(self.custom_hand)
        
        # --- REFERENCE BOARD TOGGLE ---
        self.btn_ref = QToolButton()
        self.btn_ref.setIcon(get_qicon("chalkboard"))
        self.btn_ref.setFixedSize(36, 36)
        self.btn_ref.setToolTip("Toggle Reference Board (R)")
        self.btn_ref.setCheckable(True)
        self.btn_ref.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 18px;
            }
            QPushButton:checked {
                background-color: #BA4A00;
                color: white;
            }
        """)
        self.btn_ref.clicked.connect(self.toggle_reference_board)
        self.btn_ref.setCursor(self.custom_hand)
        
        # Grouping Studio and Diagnostics at the top        
        top_btn_layout.addStretch()
        top_btn_layout.addWidget(self.btn_studio)
        top_btn_layout.addWidget(self.btn_diag)
        top_btn_layout.addWidget(self.btn_ref)
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
        
        self.btn_color.setFixedSize(32, 32)
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
        container_size, self.slider_size = self.create_slider("SIZE", 1, 500, 20, self.canvas.set_brush_size)
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
        
        self.shortcut_reset = QShortcut(QKeySequence("Ctrl+0"), self)
        self.shortcut_reset.activated.connect(self.reset_view)
        
    def decrease_brush_size(self):
        self.slider_size.setValue(max(1, self.slider_size.value() - 10))

    def increase_brush_size(self):
        self.slider_size.setValue(min(500, self.slider_size.value() + 10))

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
        self.menuBar().setVisible(False)
        
        self.custom_menubar = QMenuBar()
        view_menu = self.custom_menubar.addMenu("&View")
        
        self.diag_action = QAction("System Diagnostics", self)
        self.diag_action.setCheckable(True)
        self.diag_action.setShortcut("D")
        self.diag_action.triggered.connect(self.toggle_diagnostics)
        view_menu.addAction(self.diag_action)
        
        view_menu.addSeparator()
    
        self.ref_board_action = QAction("Reference Board", self)
        self.ref_board_action.setShortcut("R")
        self.ref_board_action.triggered.connect(self.toggle_reference_board)
        view_menu.addAction(self.ref_board_action)
        
        self.main_layout.insertWidget(1, self.custom_menubar)
        
    def toggle_reference_board(self):   
        """Open or close the reference board window and sync the UI."""
        if self.reference_board_window is None:
            self.reference_board_window = ReferenceBoardWindow()
            self.reference_board_window.show()
            self.reference_board_window.destroyed.connect(
                lambda: self.sync_ref_ui(False)
            )
        else:
            is_now_visible = not self.reference_board_window.isVisible()
            self.reference_board_window.setVisible(is_now_visible)
        
        self.sync_ref_ui(self.reference_board_window.isVisible())
        
    def sync_ref_ui(self, is_open):
        """Updates the button and menu state to match reality."""
        self.btn_ref.setChecked(is_open)
        if hasattr(self, 'ref_board_action'):
            self.ref_board_action.setChecked(is_open)
        if not is_open:
            if self.reference_board_window and not self.reference_board_window.isVisible():
                self.reference_board_window = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_D:
            self.toggle_diagnostics()
        elif event.key() == Qt.Key.Key_Z:
            self.canvas.keyPressEvent(event)
        elif event.key() == Qt.Key.Key_BracketLeft:
            self.decrease_brush_size()
        elif event.key() == Qt.Key.Key_BracketRight:
            self.increase_brush_size()
        
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        """Standard window resize handler to keep 'Islands' in place."""
        # THE FIX: We measure the ROOT frame instead of the inner container.
        # This ensures the Canvas 'Motherboard' spans the entire available area.
        root_w = self.root_container.width()
        root_h = self.root_container.height()
        
        # Subtract the Title Bar and Menu Bar heights so the canvas doesn't 
        # slide 'under' them.
        offset_y = self.title_bar.height() + self.custom_menubar.height()
        available_h = root_h - offset_y
        
        # Set the Canvas to the full available real estate
        self.canvas.setGeometry(0, offset_y, root_w, available_h)
        
        # --- POSITIONING THE ISLANDS ---
        # We use root_w and available_h for these now too!
        if not self.panels_positioned:
            self.bag_frame.setGeometry(20, offset_y + 20, 125, available_h - 40)
            self.layer_panel.setGeometry(root_w - 260, offset_y + 20, 240, available_h - 40)
            # self.panels_positioned = True # Optional: Keep False if you want them to move on every resize
            
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
        
    def reset_view(self):
        """Standardizes the view to fit the paper perfectly in the center."""
        win_h = self.root_container.height()
        if hasattr(self, 'title_bar') and self.title_bar is not None:
            win_h -= self.title_bar.height()
        if hasattr(self, 'custom_menubar') and self.custom_menubar is not None:
            win_h -= self.custom_menubar.height()
        
        win_w = self.root_container.width()
            
        scale_x = (win_w * 0.8) / self.canvas.canvas_width
        scale_y = (win_h * 0.8) / self.canvas.canvas_height
        
        new_scale = min(scale_x, scale_y, 1.0)
        self.canvas.view_scale = new_scale

        paper_w_scaled = self.canvas.canvas_width * new_scale
        paper_h_scaled = self.canvas.canvas_height * new_scale
        
        offset_x = (win_w - paper_w_scaled) / 2
        offset_y = (win_h - paper_h_scaled) / 2
        
        self.canvas.view_offset = QPoint(int(offset_x), int(offset_y))
        
        self.canvas.update()
        if self.canvas is not None:
            self.canvas.refresh_cursor()