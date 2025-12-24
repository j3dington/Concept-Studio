import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow, NewCanvasDialog # Ensure both are imported!

def main():
    # 1. Initialize the Application Environment
    app = QApplication(sys.argv)
    
    # 2. THE GATEKEEPER: Create the dialog
    dialog = NewCanvasDialog()
    
    # .exec() returns a code (Accepted or Rejected)
    # If this window doesn't show, the code below NEVER runs.
    if dialog.exec() == 1: # 1 is the value for QDialog.DialogCode.Accepted
        width, height = dialog.get_dimensions()
        
        # 3. Create the Main Motherboard with the user's specs
        window = MainWindow(width, height)
        window.show()
        
        # 4. Start the main event loop
        sys.exit(app.exec())
    else:
        # If the user hits 'Cancel' or 'X', we exit safely.
        print("LOG: User cancelled startup.")
        sys.exit(0)

if __name__ == "__main__":
    main()