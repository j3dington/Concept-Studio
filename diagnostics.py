from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer, Qt, pyqtSignal
import psutil
import os
from draggable import DraggableFrame

class DiagnosticsPanel(DraggableFrame): 
    visibility_changed = pyqtSignal(bool)
    
    def __init__(self, canvas_ref):
        super().__init__()
        self.canvas = canvas_ref
        self.setFixedWidth(180)
        
        self.setObjectName("DiagnosticsPanel")
        self.setStyleSheet("""
            #DiagnosticsPanel {
                background-color: rgba(255, 255, 255, 230);
                border: 1px solid #E0E0E0;
                border-radius: 12px;
            }
            QLabel {
                color: #555555;
                font-family: 'Segoe UI';
                font-size: 10px;
                font-weight: 600;
            }
            #TitleLabel {
                color: #BA4A00;
                font-weight: 800;
                font-size: 9px;
                letter-spacing: 1.5px;
            }
            #CloseBtn {
                background: transparent;
                color: #999;
                font-weight: bold;
                border: none;
            }
            #CloseBtn:hover { color: #BA4A00; }
        """)
        
        layout = QVBoxLayout(self)
        
        # --- HEADER ROW (Title + Close Button) ---
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel("SYSTEM")
        self.lbl_title.setObjectName("TitleLabel")
        
        self.btn_close = QPushButton("×")
        self.btn_close.setObjectName("CloseBtn")
        self.btn_close.setFixedSize(20, 20)
        self.btn_close.clicked.connect(self.hide)
        
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)
        layout.addLayout(header_layout)
        
        # --- DATA LABELS ---
        self.lbl_ram = QLabel("MEM: 0.0 MB")
        self.lbl_undo = QLabel("STEPS: 0")
        layout.addWidget(self.lbl_ram)
        layout.addWidget(self.lbl_undo)
        
        # Timer setup
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_diagnostics)
        self.timer.start(1000)
        
    def hide(self):
        super().hide()
        self.visibility_changed.emit(False)

    def show(self):
        super().show()
        self.visibility_changed.emit(True)

    def refresh_diagnostics(self):
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        self.lbl_ram.setText(f"MEM: {mem_mb:.1f} MB")
        
        # ✅ FIXED: Access the HistoryManager's undo_stack instead of canvas.undo_stack
        self.lbl_undo.setText(f"STEPS: {len(self.canvas.history.undo_stack)}")