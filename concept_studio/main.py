import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt

# Import our organized modules
from config import STYLESHEET
from logic import Layer, HistoryManager, ProjectManager
from ui import Canvas, ToolStation, LayerPanel


class ConceptStudio(QMainWindow):    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.setWindowTitle("Concept Studio v6 - Organized")
        self.resize(1200, 800)
        
        # 1. Create Canvas (the drawing area)
        self.canvas = Canvas()
        self.setCentralWidget(self.canvas)
        
        # 2. Create Tool Station (PARENTED TO CANVAS)
        # This makes it float on top of the canvas!
        self.station = ToolStation(self.canvas, parent=self.canvas)
        self.station.setGeometry(20, 20, 70, 450)
        self.station.show()
        self.station.raise_()  # Bring to front
        
        # 3. Create Layer Panel (PARENTED TO CANVAS)
        self.layer_panel = LayerPanel(self.canvas, parent=self.canvas)
        self.layer_panel.move(self.width() - 220, 20)
        self.layer_panel.show()
        self.layer_panel.raise_()  # Bring to front
        
        # Apply styling
        self.setStyleSheet(STYLESHEET)
        
        print("=" * 60)
        print("🎨 CONCEPT STUDIO v6 - Organized Edition")
        print("=" * 60)
        print("✨ Features:")
        print("   • Brush & Eraser tools")
        print("   • Move/Transform layers")
        print("   • Lasso selection")
        print("   • Undo/Redo (Ctrl+Z/Y)")
        print("   • Save/Load projects")
        print("   • Blend modes")
        print()
        print("⌨️  Shortcuts:")
        print("   B - Brush | E - Eraser | V - Move")
        print("   L - Lasso | P - Polygon Lasso")
        print("   [ ] - Brush size | Ctrl+Z/Y - Undo/Redo")
        print("=" * 60)
    
    def resizeEvent(self, event):
        """
        Handle window resizing
        
        A+ NOTE: Keep layer panel pinned to right side
        Like how icons stay in place when you resize Windows!
        """
        # Keep layer panel pinned to right
        self.layer_panel.move(self.width() - 220, 20)
        super().resizeEvent(event)


def main():
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create main window
    window = ConceptStudio()
    window.show()
    
    # Run event loop (keeps app running)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
