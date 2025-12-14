import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QDockWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QFont

# Custom Imports
from ui.startup_dialog import StartupDialog
from ui.canvas import Canvas
from ui.tool_station import ToolStation
from ui.layer_panel import LayerPanel
import styles
import config_manager
import utils

class ConceptStudio(QMainWindow):    
    def __init__(self, width=None, height=None):
        super().__init__()
        
        # 1. Config & Window Setup
        self.config = config_manager.CONFIG
        app_settings = self.config['app_settings']
        
        final_w = width if width else app_settings['initial_width']
        final_h = height if height else app_settings['initial_height']
        
        self.setWindowTitle(app_settings['title'])
        self.resize(final_w, final_h)
        self.setStyleSheet(styles.get_stylesheet())
        
        # 2. The Canvas
        self.canvas = Canvas(self, width=self.width(), height=self.height())
        self.setCentralWidget(self.canvas)
        
        # 3. The Docks
        self.station = ToolStation(self.canvas, parent=self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.station)
        
        self.layer_panel = LayerPanel(self.canvas, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layer_panel)
        
        # 4. Menus & Actions
        self.setup_actions()
        self.setup_menubar()
        self.setup_toolbar()
        
        # Start Unlocked
        self.toggle_ui_lock(False)

    def setup_actions(self):
        """Define logic for menus and buttons"""
        self.act_exit = QAction("Exit", self)
        self.act_exit.triggered.connect(self.close)

        self.act_lock = QAction("Lock Workspace", self)
        self.act_lock.setCheckable(True)
        self.act_lock.toggled.connect(self.toggle_ui_lock)

    def setup_menubar(self):
        """Create the top text menu"""
        menu = self.menuBar()
        
        file_menu = menu.addMenu("&File")
        file_menu.addAction(self.act_exit)
        
        view_menu = menu.addMenu("&View")
        view_menu.addAction(self.act_lock)
        
        # Window menu lets users bring back closed panels
        win_menu = menu.addMenu("&Window")
        win_menu.addAction(self.station.toggleViewAction())
        win_menu.addAction(self.layer_panel.toggleViewAction())

    def setup_toolbar(self):
        """Create the icon bar"""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        toolbar.addAction(self.act_lock)

    def toggle_ui_lock(self, locked):
        """Freezes or Unfreezes the panels"""
        docks = [self.station, self.layer_panel]
        for dock in docks:
            if locked:
                dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
                dock.setTitleBarWidget(None) # Can hide title bar here if desired
            else:
                dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                QDockWidget.DockWidgetFeature.DockWidgetFloatable | 
                                QDockWidget.DockWidgetFeature.DockWidgetClosable)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # === FONT LOADING ===
    # Attempt to load custom fonts. Ensure these files exist in assets/fonts/
    # If not found, it falls back to Segoe UI automatically.
    ui_font = utils.load_custom_font("DMSans-Regular.ttf")
    content_font = utils.load_custom_font("Lora-Regular.ttf")
    
    # Update Config with the REAL font names found by the system
    config_manager.CONFIG['theme']['font_family_ui'] = ui_font
    config_manager.CONFIG['theme']['font_family_content'] = content_font
    
    # Set fallback
    app.setFont(QFont(ui_font, 10))

    # === STARTUP ===
    dialog = StartupDialog()
    if dialog.exec():
        w, h = dialog.get_dimensions()
        window = ConceptStudio(width=w, height=h)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()