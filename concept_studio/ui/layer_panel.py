from PyQt6.QtWidgets import QDockWidget, QFrame, QVBoxLayout, QPushButton, QListWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt

class LayerPanel(QDockWidget):
    def __init__(self, canvas_ref, parent=None):
        super().__init__("Layers", parent)
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

        # 4. Content
        self.layer_list = QListWidget()
        self.layer_list.addItems(["Line Art", "Color", "Sketch"])
        self.layout.addWidget(self.layer_list)

        # Button Row
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("+")
        self.btn_del = QPushButton("-")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        self.layout.addLayout(btn_layout)