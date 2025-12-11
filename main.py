import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDir

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Now import the application components
from src.ui.main_window import MainWindow
from src.database.models import Database

def setup_application():
    """Set up and run the application"""
    # Initialize the application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set up application paths
    app_dir = Path(__file__).parent
    QDir.addSearchPath('icons', str(app_dir / 'assets' / 'icons'))
    
    # Initialize database
    db = Database()
    
    # Create and show main window
    window = MainWindow()
    window.showMaximized()
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    setup_application()