import math
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                            QPushButton, QHBoxLayout, QLabel, QComboBox, QSlider)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize
from draggable import DraggableFrame

class LayerPanel(DraggableFrame):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.setObjectName("LayerPanel")
        
        # Connect to the canvas signal so we refresh when layers are added/deleted
        if hasattr(self.canvas, 'layers_changed'):
            self.canvas.layers_changed.connect(self.refresh_layers)
        
        self.setup_ui()
        self.refresh_layers()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(10)
        
        # 1. HEADER
        lbl = QLabel("LAYERS")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        # 2. LAYER PROPERTIES (Opacity & Blending)
        # This section controls the 'Metadata' of the selected layer
        prop_layout = QHBoxLayout()
        
        self.blend_combo = QComboBox()
        self.blend_combo.addItems(["Normal", "Multiply", "Screen", "Overlay", "Add"])
        self.blend_combo.currentTextChanged.connect(self.on_blend_changed)
        prop_layout.addWidget(self.blend_combo)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setToolTip("Layer Opacity")
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        prop_layout.addWidget(self.opacity_slider)
        
        layout.addLayout(prop_layout)
        
        # 3. THE LIST (Where layers live)
        self.list_widget = QListWidget()
        # currentRowChanged: Fires when you click a different row
        self.list_widget.currentRowChanged.connect(self.on_row_changed)
        # itemChanged: Fires when text is edited or checkbox is toggled
        self.list_widget.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.list_widget)
        
        # 4. BOTTOM BUTTONS (Add / Delete)
        btn_layout = QHBoxLayout()
        
        # Add Button with Icon
        self.btn_add = QPushButton()
        self.btn_add.setObjectName("SmallBtn")
        self.btn_add.setFixedSize(36, 36)
        self.btn_add.setIcon(QIcon("icons/plus-circle.svg"))
        self.btn_add.setIconSize(QSize(20, 20))
        self.btn_add.setToolTip("Add New Layer")
        self.btn_add.clicked.connect(self.add_layer)
        
        # Delete Button with Icon
        self.btn_del = QPushButton()
        self.btn_del.setObjectName("SmallBtn")
        self.btn_del.setFixedSize(36, 36)
        self.btn_del.setIcon(QIcon("icons/minus-circle"))
        self.btn_del.setIconSize(QSize(20, 20))
        self.btn_del.setToolTip("Delete Active Layer")
        self.btn_del.clicked.connect(self.delete_layer)
        
        btn_layout.addStretch() 
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_del)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)

    def refresh_layers(self):
        """Syncs the UI list with the actual layers in the Canvas."""
        # Block signals so adding items doesn't trigger 'on_item_changed' accidentally
        self.list_widget.blockSignals(True) 
        self.list_widget.clear()
        
        # We iterate backwards (top-down) so the top layer in code is top in UI
        for i in range(len(self.canvas.layers) - 1, -1, -1):
            layer = self.canvas.layers[i]
            
            item = QListWidgetItem(layer.name)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            # Enable Renaming, Checking, and Selecting
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable | 
                        Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
            
            # Set Checkbox state
            state = Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked
            item.setCheckState(state)
            
            # Store the real index so we can find this layer later
            item.setData(Qt.ItemDataRole.UserRole, i)
            
            self.list_widget.addItem(item)

        # Highlight the currently active layer
        row = len(self.canvas.layers) - 1 - self.canvas.current_layer_index
        self.list_widget.setCurrentRow(row)
        
        self.list_widget.blockSignals(False)

    def on_row_changed(self, row):
        """Handles switching between layers."""
        if row < 0: return
        
        item = self.list_widget.item(row)
        real_index = item.data(Qt.ItemDataRole.UserRole)
        
        # Update Canvas
        self.canvas.current_layer_index = real_index
        
        # Update Opacity/Blend controls to match the newly selected layer
        layer = self.canvas.layers[real_index]
        
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(int(layer.opacity * 100))
        self.opacity_slider.blockSignals(False)
        
        self.blend_combo.blockSignals(True)
        self.blend_combo.setCurrentText(layer.blend_mode)
        self.blend_combo.blockSignals(False)
        
    def on_item_changed(self, item):
        """Handles Renaming and Visibility Toggles."""
        real_index = item.data(Qt.ItemDataRole.UserRole)
        layer = self.canvas.layers[real_index]
        
        # 1. Check for Rename
        if item.text() != layer.name:
            layer.name = item.text()
            
        # 2. Check for Visibility Change
        is_checked = (item.checkState() == Qt.CheckState.Checked)
        if is_checked != layer.visible:
            self.canvas.toggle_layer_visibility(real_index)

    def on_opacity_changed(self, value):
        self.canvas.set_active_layer_opacity(value / 100.0)

    def on_blend_changed(self, text):
        self.canvas.set_active_layer_blend_mode(text)

    def add_layer(self):
        self.canvas.add_new_layer()
        # Signal in canvas will trigger refresh_layers

    def delete_layer(self):
        self.canvas.delete_active_layer()
        # Signal in canvas will trigger refresh_layers