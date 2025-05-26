#!/usr/bin/env python3
"""
Test script for PyQt6 GUI
"""

import sys
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

def test_gui():
    """Test the PyQt6 GUI"""
    try:
        # Import the GUI
        from opensuperwhisper_gui_pyqt6 import OpenSuperWhisperGUI
        
        app = QApplication(sys.argv)
        
        # Create window
        window = OpenSuperWhisperGUI()
        window.show()
        
        print("PyQt6 GUI created successfully!")
        print("Window title:", window.windowTitle())
        print("Window size:", window.size().width(), "x", window.size().height())
        
        # Close after 3 seconds for testing
        QTimer.singleShot(3000, app.quit)
        
        # Run app
        app.exec()
        
        print("PyQt6 GUI test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error testing PyQt6 GUI: {e}")
        return False

if __name__ == "__main__":
    success = test_gui()
    sys.exit(0 if success else 1)
