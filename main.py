import sys
import os
import traceback
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QDir, Qt

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def show_error_message(title, message):
    """エラーメッセージを表示する"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setWindowFlags(Qt.WindowStaysOnTopHint)
    msg.exec()

def setup_application():
    """アプリケーションのセットアップと実行"""
    try:
        print("アプリケーションを初期化中...")
        app = QApplication(sys.argv)
        
        # アプリケーションスタイルの設定
        app.setStyle('Fusion')
        
        # アプリケーションパスの設定
        app_dir = Path(__file__).parent
        icons_path = app_dir / 'assets' / 'icons'
        print(f"アイコンパス: {icons_path}")
        
        # アイコンパスの確認
        if not icons_path.exists():
            print(f"警告: アイコンパスが存在しません: {icons_path}")
            # アイコンパスがなくても続行
        
        QDir.addSearchPath('icons', str(icons_path))
        
        # データベースの初期化
        print("データベースを初期化中...")
        try:
            from src.database.models import Database
            db = Database()
            print("データベースの初期化が完了しました")
        except Exception as e:
            error_msg = f"データベースの初期化に失敗しました:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            show_error_message("データベースエラー", "データベースの初期化中にエラーが発生しました。\n詳細はコンソールを確認してください。")
            # データベースがなくてもアプリケーションは続行
        
        # メインウィンドウの作成と表示
        print("メインウィンドウを作成中...")
        try:
            from src.ui.main_window import MainWindow
            window = MainWindow()
            window.showMaximized()
            print("メインウィンドウの表示に成功しました")
        except Exception as e:
            error_msg = f"メインウィンドウの作成中にエラーが発生しました:\n{str(e)}\n\n{traceback.format_exc()}"
            print(error_msg)
            show_error_message("UIエラー", "メインウィンドウの作成中にエラーが発生しました。\n詳細はコンソールを確認してください。")
            return 1
        
        # アプリケーションの実行
        print("アプリケーションを起動します")
        return app.exec()
        
    except Exception as e:
        error_msg = f"致命的なエラーが発生しました:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        show_error_message("致命的なエラー", "アプリケーションの起動中に予期せぬエラーが発生しました。\n詳細はコンソールを確認してください。")
        return 1

if __name__ == "__main__":
    sys.exit(setup_application())