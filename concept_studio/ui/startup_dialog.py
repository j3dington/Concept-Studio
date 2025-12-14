from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QSpinBox, 
                            QPushButton, QHBoxLayout, QFormLayout)
from PyQt6.QtCore import Qt

class StartupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Project")
        self.setFixedSize(300, 200)
        self.selected_width = 1920
        self.selected_height = 1080
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Concept Studio")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        self.spin_width = QSpinBox()
        self.spin_width.setRange(100, 8000)
        self.spin_width.setValue(1920)
        self.spin_width.setSuffix(" px")
        
        self.spin_height = QSpinBox()
        self.spin_height.setRange(100, 8000)
        self.spin_height.setValue(1080)
        self.spin_height.setSuffix(" px")
        
        form_layout.addRow("Width:", self.spin_width)
        form_layout.addRow("Height:", self.spin_height)
        layout.addLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_create = QPushButton("Create Canvas")
        self.btn_create.clicked.connect(self.accept) # 'accept' closes dialog with Success code
        self.btn_create.setStyleSheet("background-color: #d4af37; color: black; font-weight: bold;")
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject) # 'reject' closes with Failure code
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_create)
        layout.addLayout(btn_layout)

    def get_dimensions(self):
        return self.spin_width.value(), self.spin_height.value()