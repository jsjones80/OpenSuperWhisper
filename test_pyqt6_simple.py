#!/usr/bin/env python3
"""Test simple PyQt6 app to debug crash"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen

class TestButton(QPushButton):
    def __init__(self):
        super().__init__()
        self.setText("")
        self.setFixedSize(50, 50)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor("#ef4444")))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.drawEllipse(self.rect().center(), 8, 8)
        painter.end()

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test")
        self.setGeometry(100, 100, 300, 200)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Test custom button
        btn = TestButton()
        layout.addWidget(btn)
        
        widget.setLayout(layout)
        self.setCentralWidget(widget)

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()