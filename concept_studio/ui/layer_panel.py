"""
Layer Panel - Layer Management Interface
"""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QListWidget, 
                            QListWidgetItem, QPushButton, QSlider, QComboBox, QHBoxLayout)
from PyQt6.QtCore import Qt
from config import BLEND_MODES


class LayerPanel(QFrame):
    def __init__(self, canvas_ref, parent=None):
        super().__init__(parent)
        self.canvas = canvas_ref
        self.setObjectName("LayerPanel")
        self.setFixedWidth(220)
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 20, 15, 20)
        
        layout.addWidget(QLabel("LAYERS"))
        self.combo_blend = QComboBox()
        self.combo_blend.addItems(BLEND_MODES.keys())
        self.combo_blend.setStyleSheet("QComboBox { background-color: rgba(255,255,255,0.05); color: #e0e0e0; border: none; padding: 5px; } QComboBox QAbstractItemView { background-color: #2d2d2d; selection-background-color: #d4af37; }")
        self.combo_blend.currentTextChanged.connect(self.change_blend_mode)
        layout.addWidget(self.combo_blend)
        
        self.list_widget = QListWidget()
        self.refresh_list()
        self.list_widget.currentRowChanged.connect(self.change_layer)
        layout.addWidget(self.list_widget)
        
        row1 = QHBoxLayout()
        self.btn_hide = QPushButton("👁️")
        self.btn_hide.clicked.connect(self.toggle_visibility)
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setObjectName("DangerBtn")
        self.btn_delete.clicked.connect(self.delete_layer)
        row1.addWidget(self.btn_hide); row1.addWidget(self.btn_delete)
        layout.addLayout(row1)
        
        btn_add = QPushButton(" + New Layer "); btn_add.setStyleSheet("background-color: rgba(255,255,255,0.05);")
        btn_add.clicked.connect(self.add_layer)
        layout.addWidget(btn_add)

    def change_blend_mode(self, mode_text):
        if 0 <= self.canvas.active_layer_index < len(self.canvas.layers):
            self.canvas.layers[self.canvas.active_layer_index].blend_mode = mode_text
            self.canvas.update()

    def change_layer(self, row):
        if row < 0: return
        real_index = (len(self.canvas.layers) - 1) - row
        if 0 <= real_index < len(self.canvas.layers):
            self.canvas.active_layer_index = real_index
            self.btn_hide.setText("👁️" if self.canvas.layers[real_index].visible else "○")
            self.combo_blend.blockSignals(True)
            self.combo_blend.setCurrentText(self.canvas.layers[real_index].blend_mode)
            self.combo_blend.blockSignals(False)

    def toggle_visibility(self):
        layer = self.canvas.layers[self.canvas.active_layer_index]
        layer.visible = not layer.visible
        self.btn_hide.setText("👁️" if layer.visible else "○")
        self.canvas.update()

    def delete_layer(self):
        if self.canvas.delete_active_layer(): self.refresh_list()
        else: self.btn_delete.setText("⚠️ 1 Layer!")

    def add_layer(self):
        self.canvas.add_layer()
        self.refresh_list()

    def refresh_list(self):
        self.list_widget.clear()
        for i in range(len(self.canvas.layers) - 1, -1, -1):
            item = QListWidgetItem(self.canvas.layers[i].name)
            self.list_widget.addItem(item)
            if i == self.canvas.active_layer_index: self.list_widget.setCurrentItem(item)
