from PyQt6.QtWidgets import QDockWidget, QFrame, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt

class ToolStation(QDockWidget):
    def __init__(self, canvas_ref, parent=None):
        super().__init__("Tools", parent)
        self.canvas = canvas_ref
        
        # 1. Dock Config
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        # 2. Container
        self.container = QFrame()
        self.container.setObjectName("PanelContent")
        self.setWidget(self.container)

        # 3. Layout
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 4. Content
        title = QLabel("TOOLS")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; opacity: 0.5; font-size: 10px;")
        self.layout.addWidget(title)

        tools = ["B", "E", "S", "F"]
        for t in tools:
            btn = QPushButton(t)
            btn.setFixedSize(40, 40)
            self.layout.addWidget(btn)

        self.layout.addStretch()