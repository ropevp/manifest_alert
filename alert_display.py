# Basic import test
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class AlertDisplay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Manifest Control Center")
        self.setMinimumSize(1200, 800)
        
        layout = QVBoxLayout()
        label = QLabel("SpaceX-Style Mission Control Interface")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

print("AlertDisplay class defined")