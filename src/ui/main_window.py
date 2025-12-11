# src/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon

class SidebarButton(QPushButton):
    """Custom button for the sidebar"""
    def __init__(self, text: str, icon_path: str = None, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        
        # Set icon if provided
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))
        
        # Style
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: none;
                border-radius: 5px;
                margin: 2px 5px;
            }
            QPushButton:checked, QPushButton:hover {
                background-color: #e1e1e1;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)

class MainWindow(QMainWindow):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("学術論文管理システム")
        self.setMinimumSize(1200, 800)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout (sidebar + content)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack, 1)  # Take remaining space
        
        # Add some placeholder pages
        self._setup_pages()
        
        # Connect signals
        self._connect_signals()
    
    def _create_sidebar(self) -> QWidget:
        """サイドバーウィジェットを作成して返す"""
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-right: 1px solid #ddd;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(5, 20, 5, 20)
        layout.setSpacing(5)
        
        # アプリケーションタイトル
        title = QLabel("論文管理")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px 15px;
                color: #333;
            }
        """)
        layout.addWidget(title)
        
        # ナビゲーションボタン
        self.nav_buttons = {}
        nav_items = [
            ("ホーム", "home", "home"),
            ("論文一覧", "list", "list"),
            ("論文登録", "add", "plus"),
            ("検索", "search", "search"),
            ("統計", "stats", "bar-chart"),
            ("設定", "settings", "settings")
        ]
        
        for text, key, icon in nav_items:
            try:
                # アイコン付きでボタンを作成（アイコンが読み込めない場合はテキストのみ）
                icon_path = f":/icons/{icon}.png"
                btn = SidebarButton(text, icon_path)
            except Exception as e:
                print(f"アイコンの読み込みに失敗しました: {icon}.png - {str(e)}")
                # アイコンなしでボタンを作成
                btn = SidebarButton(text)
                
            self.nav_buttons[key] = btn
            layout.addWidget(btn)
        
        # ボタンを上部に配置するためのスペーサー
        layout.addStretch()
        
        return sidebar
    
    def _setup_pages(self):
        """Set up the main content pages"""
        # Add placeholder pages
        self.pages = {}
        
        for page_name in ["home", "list", "add", "search", "stats", "settings"]:
            page = QLabel(f"This is the {page_name.replace('_', ' ').title()} page")
            page.setAlignment(Qt.AlignCenter)
            self.pages[page_name] = page
            self.content_stack.addWidget(page)
    
    def _connect_signals(self):
        """Connect UI signals to slots"""
        # Connect navigation buttons to page switching
        self.nav_buttons["home"].clicked.connect(lambda: self.switch_page("home"))
        self.nav_buttons["list"].clicked.connect(lambda: self.switch_page("list"))
        self.nav_buttons["add"].clicked.connect(lambda: self.switch_page("add"))
        self.nav_buttons["search"].clicked.connect(lambda: self.switch_page("search"))
        self.nav_buttons["stats"].clicked.connect(lambda: self.switch_page("stats"))
        self.nav_buttons["settings"].clicked.connect(lambda: self.switch_page("settings"))
        
        # Select the home page by default
        self.nav_buttons["home"].setChecked(True)
        self.switch_page("home")
    
    def switch_page(self, page_name: str):
        """Switch to the specified page"""
        if page_name in self.pages:
            # Update button states
            for btn in self.nav_buttons.values():
                btn.setChecked(False)
            self.nav_buttons[page_name].setChecked(True)
            
            # Switch page
            self.content_stack.setCurrentWidget(self.pages[page_name])