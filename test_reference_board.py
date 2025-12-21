"""
Test script for Reference Board - Run this to see if it works standalone
"""

import sys
from PyQt6.QtWidgets import QApplication

# Try importing the reference board
try:
    from reference_board_window import ReferenceBoardWindow
    print("✅ Successfully imported ReferenceBoardWindow")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("Make sure reference_board_window.py is in the same folder!")
    sys.exit(1)

try:
    from reference_board import ReferenceBoard
    print("✅ Successfully imported ReferenceBoard")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("Make sure reference_board.py is in the same folder!")
    sys.exit(1)

try:
    from reference_items import ImageItem, StickyNote
    print("✅ Successfully imported reference items")
except ImportError as e:
    print(f"❌ IMPORT ERROR: {e}")
    print("Make sure reference_items.py is in the same folder!")
    sys.exit(1)

# If we got here, imports work! Try running it
print("\n🚀 Starting Reference Board test...")

app = QApplication(sys.argv)

try:
    window = ReferenceBoardWindow()
    print("✅ Window created successfully")
    
    window.show()
    print("✅ Window shown successfully")
    print("\n💡 Try these:")
    print("   1. Drag an image file from your desktop onto the board")
    print("   2. Click the note button to add a sticky note")
    print("   3. Select an item and try the color picker")
    
    sys.exit(app.exec())
    
except Exception as e:
    print(f"❌ RUNTIME ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
