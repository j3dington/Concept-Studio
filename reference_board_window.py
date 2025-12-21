"""
Reference Board Window - The complete UI for the reference board feature
This is like a separate window that artists can keep open while painting.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QToolButton, QFileDialog, QInputDialog, QLabel, QMessageBox, QMenu)
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut, QAction
from PyQt6.QtCore import Qt, QSize

from reference_board import ReferenceBoard
from reference_items import StickyNote

# Try to import icon system, but don't fail if it doesn't exist
try:
    from assets import get_qicon
except ImportError:
    print("Warning: assets.py not found, buttons will have no icons")
    def get_qicon(name):
        """Dummy function if assets not available"""
        from PyQt6.QtGui import QIcon
        return QIcon()  # Return empty icon


class ReferenceBoardWindow(QMainWindow):
    """
    The complete reference board window.
    This can be opened alongside the main Gesso window.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reference Board - Gesso")
        self.resize(1200, 800)
        
        # Create the main board
        self.board = ReferenceBoard()
        
        # Build UI
        self.setup_ui()
        self.setup_shortcuts()
        
        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2D2D2D;
            }
            QToolButton {
                background-color: #3D3D3D;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                color: #FFFFFF;
            }
            QToolButton:hover {
                background-color: #4D4D4D;
                border: 1px solid #777777;
            }
            QToolButton:pressed {
                background-color: #2D2D2D;
            }
            #InfoLabel {
                color: #AAAAAA;
                font-size: 10px;
                padding: 2px 8px;
            }
        """)
    
    def setup_ui(self):
        """Build the user interface."""
        # Main container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # The board itself
        layout.addWidget(self.board)
        
        # Status bar with helpful info
        info_bar = self.create_info_bar()
        layout.addWidget(info_bar)
        
        self.setCentralWidget(container)
    
    def create_toolbar(self):
        """Create the toolbar with all the tools."""
        toolbar = QWidget()
        toolbar.setObjectName("Toolbar")
        toolbar.setStyleSheet("background-color: #3D3D3D; padding: 3px;")
        toolbar.setMaximumHeight(30)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 3, 8, 3)
        layout.setSpacing(3)
        
        # --- FILE OPERATIONS ---
        
        # Add Image button
        self.btn_add_image = QToolButton()
        self.btn_add_image.setIcon(get_qicon("image"))
        self.btn_add_image.setIconSize(QSize(16, 16))
        self.btn_add_image.setToolTip("Add Image (Ctrl+I)")
        self.btn_add_image.clicked.connect(self.add_image_dialog)
        layout.addWidget(self.btn_add_image)
        
        # Add Sticky Note button
        self.btn_add_note = QToolButton()
        self.btn_add_note.setIcon(get_qicon("file-text"))
        self.btn_add_note.setIconSize(QSize(16, 16))
        self.btn_add_note.setToolTip("Add Sticky Note (Ctrl+N)")
        self.btn_add_note.clicked.connect(self.add_note_dialog)
        layout.addWidget(self.btn_add_note)
        
        # Note color picker (dropdown menu)
        self.btn_note_color = QToolButton()
        self.btn_note_color.setText("🎨")
        self.btn_note_color.setToolTip("Change Note Color")
        self.btn_note_color.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        # Create color menu
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        color_menu = QMenu(self)
        
        colors = {
            "Yellow": "yellow",
            "Pink": "pink", 
            "Blue": "blue",
            "Green": "green",
            "Orange": "orange"
        }
        
        for name, color in colors.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, c=color: self.change_note_color(c))
            color_menu.addAction(action)
        
        self.btn_note_color.setMenu(color_menu)
        layout.addWidget(self.btn_note_color)
        
        layout.addSpacing(6)
        
        # --- EDIT OPERATIONS ---
        
        # Delete selected
        self.btn_delete = QToolButton()
        self.btn_delete.setIcon(get_qicon("trash"))
        self.btn_delete.setIconSize(QSize(16, 16))
        self.btn_delete.setToolTip("Delete Selected (Delete)")
        self.btn_delete.clicked.connect(self.board.delete_selected)
        layout.addWidget(self.btn_delete)
        
        # Clear all
        self.btn_clear = QToolButton()
        self.btn_clear.setIcon(get_qicon("x-circle"))
        self.btn_clear.setIconSize(QSize(16, 16))
        self.btn_clear.setToolTip("Clear Board")
        self.btn_clear.clicked.connect(self.clear_board)
        layout.addWidget(self.btn_clear)
        
        layout.addSpacing(6)
        
        # --- SAVE / LOAD ---
        
        # Save board
        self.btn_save = QToolButton()
        self.btn_save.setIcon(get_qicon("save"))
        self.btn_save.setIconSize(QSize(16, 16))
        self.btn_save.setToolTip("Save Board (Ctrl+S)")
        self.btn_save.clicked.connect(self.save_board_dialog)
        layout.addWidget(self.btn_save)
        
        # Load board
        self.btn_load = QToolButton()
        self.btn_load.setIcon(get_qicon("folder-open"))
        self.btn_load.setIconSize(QSize(16, 16))
        self.btn_load.setToolTip("Load Board (Ctrl+O)")
        self.btn_load.clicked.connect(self.load_board_dialog)
        layout.addWidget(self.btn_load)
        
        layout.addStretch()
        
        # --- VIEW CONTROLS ---
        
        # Background color picker
        self.btn_bg_color = QToolButton()
        self.btn_bg_color.setText("BG")
        self.btn_bg_color.setToolTip("Change Background Color")
        self.btn_bg_color.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        # Create background color menu
        bg_menu = QMenu(self)
        
        bg_colors = {
            "Light Gray": "light_gray",
            "Dark Gray": "dark_gray",
            "White": "white"
        }
        
        for name, color in bg_colors.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, c=color: self.change_background_color(c))
            bg_menu.addAction(action)
        
        self.btn_bg_color.setMenu(bg_menu)
        layout.addWidget(self.btn_bg_color)
        
        layout.addSpacing(3)
        
        # Reset view
        self.btn_reset_view = QToolButton()
        self.btn_reset_view.setIcon(get_qicon("maximize"))
        self.btn_reset_view.setIconSize(QSize(16, 16))
        self.btn_reset_view.setToolTip("Reset View (Home)")
        self.btn_reset_view.clicked.connect(self.reset_view)
        layout.addWidget(self.btn_reset_view)
        
        return toolbar
    
    def create_info_bar(self):
        """Create the info bar at the bottom."""
        info_bar = QWidget()
        info_bar.setObjectName("InfoBar")
        info_bar.setStyleSheet("background-color: #2D2D2D;")
        info_bar.setMaximumHeight(20)
        
        layout = QHBoxLayout(info_bar)
        layout.setContentsMargins(8, 2, 8, 2)
        
        self.lbl_info = QLabel("💡 Drag images | Double-click notes to edit | Ctrl+D duplicate | Delete key or click X")
        self.lbl_info.setObjectName("InfoLabel")
        layout.addWidget(self.lbl_info)
        
        layout.addStretch()
        
        self.lbl_item_count = QLabel("Items: 0")
        self.lbl_item_count.setObjectName("InfoLabel")
        layout.addWidget(self.lbl_item_count)
        
        # Update item count when items change
        self.board.items_changed.connect(self.update_item_count)
        
        return info_bar
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Add image
        QShortcut(QKeySequence("Ctrl+I"), self, self.add_image_dialog)
        
        # Add note
        QShortcut(QKeySequence("Ctrl+N"), self, self.add_note_dialog)
        
        # Duplicate
        QShortcut(QKeySequence("Ctrl+D"), self, self.board.duplicate_selected)
        
        # Save
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_board_dialog)
        
        # Load
        QShortcut(QKeySequence("Ctrl+O"), self, self.load_board_dialog)
        
        # Reset view
        QShortcut(QKeySequence("Home"), self, self.reset_view)
    
    # --- ACTIONS ---
    
    def add_image_dialog(self):
        """Open file dialog to add an image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Reference Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
        )
        
        if file_path:
            self.board.add_image(file_path)
    
    def add_note_dialog(self):
        """Open dialog to add a sticky note."""
        text, ok = QInputDialog.getText(
            self,
            "New Sticky Note",
            "Enter note text:",
            text="Type your note here..."
        )
        
        if ok:
            self.board.add_sticky_note(text=text)
    
    def save_board_dialog(self):
        """Save the board to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Reference Board",
            "",
            "Reference Board (*.refboard)"
        )
        
        if file_path:
            self.board.save_board(file_path)
            QMessageBox.information(self, "Saved", f"Board saved to:\n{file_path}")
    
    def load_board_dialog(self):
        """Load a board from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Reference Board",
            "",
            "Reference Board (*.refboard)"
        )
        
        if file_path:
            self.board.load_board(file_path)
            QMessageBox.information(self, "Loaded", f"Board loaded from:\n{file_path}")
    
    def clear_board(self):
        """Clear all items from the board."""
        reply = QMessageBox.question(
            self,
            "Clear Board",
            "Are you sure you want to clear all items?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.board.items.clear()
            self.board.items_changed.emit()
            self.board.update()
    
    def reset_view(self):
        """Reset pan and zoom to default."""
        self.board.view_offset = QPoint(0, 0)
        self.board.view_scale = 1.0
        self.board.update()
    
    def update_item_count(self):
        """Update the item count label."""
        count = len(self.board.items)
        self.lbl_item_count.setText(f"Items: {count}")
    
    def change_note_color(self, color_name: str):
        """Change the color of selected sticky notes."""
        print(f"DEBUG: change_note_color called with color: {color_name}")
        print(f"DEBUG: Number of selected items: {len(self.board.selected_items)}")
        
        changed = False
        for item in self.board.selected_items:
            print(f"DEBUG: Checking item type: {type(item).__name__}")
            if isinstance(item, StickyNote):
                print(f"DEBUG: Changing sticky note color to {color_name}")
                item.set_color(color_name)
                changed = True
        
        if changed:
            print("DEBUG: Updating board display")
            self.board.update()
        else:
            print("DEBUG: No sticky notes were selected to change color")
    
    def change_background_color(self, color_name: str):
        """Change the board background color."""
        print(f"DEBUG: change_background_color called with color: {color_name}")
        self.board.set_background_color(color_name)