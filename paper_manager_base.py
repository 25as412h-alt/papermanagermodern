"""
学術論文管理アプリケーション
題名、著者、年、タグ、要約、本文を管理・検索するアプリケーション
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from datetime import datetime
import os
import csv


# ================================
# データベース設定
# ================================

def init_db():
    """データベース初期化"""
    conn = sqlite3.connect('papers.db')
    cursor = conn.cursor()
    
    # 論文テーブル作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_en TEXT,
            authors TEXT,
            authors_en TEXT,
            year INTEGER,
            tags TEXT,
            summary TEXT,
            fulltext TEXT,
            original_file TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


# ================================
# データベース操作クラス
# ================================

class PaperDatabase:
    """論文データベース操作クラス"""
    
    def __init__(self, db_name='papers.db'):
        self.db_name = db_name
    
    def get_connection(self):
        """データベース接続取得"""
        return sqlite3.connect(self.db_name)
    
    def add_paper(self, title, title_en, authors, authors_en, year, 
                  tags, summary, fulltext, original_file):
        """論文追加"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO papers 
            (title, title_en, authors, authors_en, year, tags, 
             summary, fulltext, original_file, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, title_en, authors, authors_en, year, tags,
              summary, fulltext, original_file, now, now))
        
        conn.commit()
        paper_id = cursor.lastrowid
        conn.close()
        return paper_id
    
    def update_paper(self, paper_id, title, title_en, authors, authors_en, 
                     year, tags, summary, fulltext, original_file):
        """論文更新"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            UPDATE papers
            SET title=?, title_en=?, authors=?, authors_en=?, year=?,
                tags=?, summary=?, fulltext=?, original_file=?, updated_at=?
            WHERE id=?
        ''', (title, title_en, authors, authors_en, year, tags,
              summary, fulltext, original_file, now, paper_id))
        
        conn.commit()
        conn.close()
    
    def delete_paper(self, paper_id):
        """論文削除"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM papers WHERE id=?', (paper_id,))
        conn.commit()
        conn.close()
    
    def get_all_papers(self):
        """全論文取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM papers ORDER BY year DESC, title_en')
        papers = cursor.fetchall()
        conn.close()
        return papers
    
    def get_paper_by_id(self, paper_id):
        """ID指定で論文取得"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM papers WHERE id=?', (paper_id,))
        paper = cursor.fetchone()
        conn.close()
        return paper
    
    def search_papers(self, title='', authors='', year_from=None, 
                     year_to=None, tags=''):
        """範囲検索"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM papers WHERE 1=1'
        params = []
        
        if title:
            query += ' AND (title LIKE ? OR title_en LIKE ?)'
            params.extend([f'%{title}%', f'%{title}%'])
        
        if authors:
            query += ' AND (authors LIKE ? OR authors_en LIKE ?)'
            params.extend([f'%{authors}%', f'%{authors}%'])
        
        if year_from:
            query += ' AND year >= ?'
            params.append(year_from)
        
        if year_to:
            query += ' AND year <= ?'
            params.append(year_to)
        
        if tags:
            query += ' AND tags LIKE ?'
            params.append(f'%{tags}%')
        
        query += ' ORDER BY year DESC, title_en'
        
        cursor.execute(query, params)
        papers = cursor.fetchall()
        conn.close()
        return papers
    
    def fulltext_search(self, keyword):
        """全文検索"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM papers 
            WHERE summary LIKE ? OR fulltext LIKE ?
            ORDER BY year DESC, title_en
        ''', (f'%{keyword}%', f'%{keyword}%'))
        
        papers = cursor.fetchall()
        conn.close()
        return papers


# ================================
# メインアプリケーションクラス
# ================================

class PaperManagerApp(tk.Tk):
    """論文管理アプリケーション メインクラス"""
    
    def __init__(self):
        super().__init__()
        
        # 基本設定
        self.title("学術論文管理システム")
        self.geometry("1400x800")
        self.configure(bg='#f0f0f0')
        
        # データベース初期化
        self.db = PaperDatabase()
        
        # UI作成
        self._create_menu()
        self._create_widgets()
        
    def _create_menu(self):
        """メニューバー作成"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="データベースバックアップ", 
                            command=self._backup_database)
        file_menu.add_command(label="CSVエクスポート", 
                            command=self._export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self._show_help)
        help_menu.add_command(label="バージョン情報", command=self._show_about)
    
    def _create_widgets(self):
        """メインUI構築"""
        # ノートブック(タブ)作成
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)
        
        # スタイル設定
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10])
        
        # 各タブのフレーム作成
        self.tab_input = ttk.Frame(self.notebook)
        self.tab_list = ttk.Frame(self.notebook)
        self.tab_edit = ttk.Frame(self.notebook)
        self.tab_range_search = ttk.Frame(self.notebook)
        self.tab_fulltext_search = ttk.Frame(self.notebook)
        
        # タブ追加
        self.notebook.add(self.tab_input, text="📝 論文登録")
        self.notebook.add(self.tab_list, text="📚 一覧表示")
        self.notebook.add(self.tab_edit, text="✏️ 編集・削除")
        self.notebook.add(self.tab_range_search, text="🔍 範囲検索")
        self.notebook.add(self.tab_fulltext_search, text="📄 全文検索")
        
        # 各タブの初期化(後で実装)
        self._init_input_tab()
        self._init_list_tab()
        self._init_edit_tab()
        self._init_range_search_tab()
        self._init_fulltext_search_tab()
    
    def _init_input_tab(self):
        """論文登録タブ初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.tab_input)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 左側: 入力フォーム
        left_frame = ttk.LabelFrame(main_frame, text="論文情報入力", padding=15)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 右側: 本文プレビュー
        right_frame = ttk.LabelFrame(main_frame, text="本文プレビュー", padding=15)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        main_frame.columnconfigure(0, weight=2)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)
        
        # --- 入力フォーム ---
        row = 0
        
        # 題名
        ttk.Label(left_frame, text="題名:*", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=5)
        self.input_title = ttk.Entry(left_frame, width=40)
        self.input_title.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 題名(英)
        ttk.Label(left_frame, text="題名(英):").grid(
            row=row, column=0, sticky="w", pady=5)
        self.input_title_en = ttk.Entry(left_frame, width=40)
        self.input_title_en.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 著者
        ttk.Label(left_frame, text="著者:*", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=5)
        self.input_authors = ttk.Entry(left_frame, width=40)
        self.input_authors.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(left_frame, text="(複数著者はコンマ区切り)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row+1, column=1, sticky="w")
        row += 2
        
        # 著者(英)
        ttk.Label(left_frame, text="著者(英):").grid(
            row=row, column=0, sticky="w", pady=5)
        self.input_authors_en = ttk.Entry(left_frame, width=40)
        self.input_authors_en.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(left_frame, text="(複数著者はコンマ区切り)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row+1, column=1, sticky="w")
        row += 2
        
        # 年
        ttk.Label(left_frame, text="発表年:*", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=5)
        self.input_year = ttk.Entry(left_frame, width=40)
        self.input_year.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # タグ
        ttk.Label(left_frame, text="タグ:").grid(
            row=row, column=0, sticky="w", pady=5)
        self.input_tags = ttk.Entry(left_frame, width=40)
        self.input_tags.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(left_frame, text="(複数タグはコンマ区切り)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row+1, column=1, sticky="w")
        row += 2
        
        # ファイル選択
        ttk.Label(left_frame, text="テキストファイル:").grid(
            row=row, column=0, sticky="w", pady=5)
        file_frame = ttk.Frame(left_frame)
        file_frame.grid(row=row, column=1, sticky="ew", pady=5)
        
        self.input_file_path = ttk.Entry(file_frame, width=30)
        self.input_file_path.pack(side="left", fill="x", expand=True)
        
        ttk.Button(file_frame, text="参照", 
                  command=self._browse_file).pack(side="left", padx=(5, 0))
        row += 1
        
        # ファイル読み込みボタン
        ttk.Button(left_frame, text="📂 ファイル読み込み", 
                  command=self._load_file).grid(
            row=row, column=1, sticky="ew", pady=10)
        row += 1
        
        # 要約入力
        ttk.Label(left_frame, text="要約:").grid(
            row=row, column=0, sticky="nw", pady=5)
        
        summary_frame = ttk.Frame(left_frame)
        summary_frame.grid(row=row, column=1, sticky="ew", pady=5)
        
        self.input_summary = scrolledtext.ScrolledText(
            summary_frame, width=40, height=6, wrap=tk.WORD)
        self.input_summary.pack(fill="both", expand=True)
        row += 1
        
        left_frame.columnconfigure(1, weight=1)
        
        # ボタンエリア
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="💾 保存", 
                  command=self._save_paper, 
                  width=15).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="🔄 クリア", 
                  command=self._clear_input_form, 
                  width=15).pack(side="left", padx=5)
        
        # --- 本文プレビュー ---
        preview_label_frame = ttk.Frame(right_frame)
        preview_label_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(preview_label_frame, text="読み込まれた本文:", 
                 font=('Arial', 10, 'bold')).pack(side="left")
        
        self.char_count_label = ttk.Label(
            preview_label_frame, text="0 文字", foreground='gray')
        self.char_count_label.pack(side="right")
        
        self.input_fulltext = scrolledtext.ScrolledText(
            right_frame, wrap=tk.WORD, width=60, height=30)
        self.input_fulltext.pack(fill="both", expand=True)
        
        # 本文カウント更新用バインド
        self.input_fulltext.bind('<<Modified>>', self._update_char_count)
    
    def _init_list_tab(self):
        """一覧表示タブ初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.tab_list)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 上部: ツールバー
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(toolbar_frame, text="登録論文一覧", 
                 font=('Arial', 12, 'bold')).pack(side="left")
        
        self.list_count_label = ttk.Label(toolbar_frame, text="0 件", 
                                         foreground='gray')
        self.list_count_label.pack(side="left", padx=10)
        
        ttk.Button(toolbar_frame, text="🔄 更新", 
                  command=self._refresh_list).pack(side="right", padx=5)
        
        ttk.Button(toolbar_frame, text="📄 詳細表示", 
                  command=self._show_paper_detail).pack(side="right", padx=5)
        
        # 中央: テーブル
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill="both", expand=True)
        
        # スクロールバー
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # Treeview作成
        columns = ('id', 'title', 'authors', 'year', 'tags', 'created_at')
        self.list_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # カラム設定
        self.list_tree.heading('id', text='ID')
        self.list_tree.heading('title', text='題名')
        self.list_tree.heading('authors', text='著者')
        self.list_tree.heading('year', text='年')
        self.list_tree.heading('tags', text='タグ')
        self.list_tree.heading('created_at', text='登録日時')
        
        self.list_tree.column('id', width=50, anchor='center')
        self.list_tree.column('title', width=300, anchor='w')
        self.list_tree.column('authors', width=200, anchor='w')
        self.list_tree.column('year', width=80, anchor='center')
        self.list_tree.column('tags', width=200, anchor='w')
        self.list_tree.column('created_at', width=150, anchor='center')
        
        y_scrollbar.config(command=self.list_tree.yview)
        x_scrollbar.config(command=self.list_tree.xview)
        
        self.list_tree.pack(fill="both", expand=True)
        
        # ダブルクリックで詳細表示
        self.list_tree.bind('<Double-1>', lambda e: self._show_paper_detail())
        
        # 初期データ読み込み
        self._refresh_list()
    
    def _init_edit_tab(self):
        """編集・削除タブ初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.tab_edit)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 左側: 論文選択エリア
        left_frame = ttk.LabelFrame(main_frame, text="論文選択", padding=15)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # 右側: 編集フォーム
        right_frame = ttk.LabelFrame(main_frame, text="編集フォーム", padding=15)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        # --- 左側: 論文リスト ---
        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill="x", pady=(0, 10))
        
        ttk.Label(toolbar, text="登録論文", 
                 font=('Arial', 10, 'bold')).pack(side="left")
        
        self.edit_count_label = ttk.Label(toolbar, text="0 件", 
                                          foreground='gray')
        self.edit_count_label.pack(side="left", padx=10)
        
        ttk.Button(toolbar, text="🔄", 
                  command=self._refresh_edit_list, 
                  width=3).pack(side="right")
        
        # リストボックスとスクロールバー
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.edit_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Arial', 10)
        )
        self.edit_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.edit_listbox.yview)
        
        # 選択時のイベント
        self.edit_listbox.bind('<<ListboxSelect>>', self._on_edit_select)
        
        # --- 右側: 編集フォーム ---
        # スクロール可能なフレーム
        canvas = tk.Canvas(right_frame, highlightthickness=0)
        scrollbar_right = ttk.Scrollbar(right_frame, orient="vertical", 
                                       command=canvas.yview)
        self.edit_form_frame = ttk.Frame(canvas)
        
        self.edit_form_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.edit_form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_right.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_right.pack(side="right", fill="y")
        
        # フォーム要素
        row = 0
        
        # 選択中のID表示
        ttk.Label(self.edit_form_frame, text="選択中のID:", 
                 font=('Arial', 9)).grid(row=row, column=0, sticky="w", pady=5)
        self.edit_id_label = ttk.Label(self.edit_form_frame, text="―", 
                                       font=('Arial', 9, 'bold'))
        self.edit_id_label.grid(row=row, column=1, sticky="w", pady=5)
        row += 1
        
        ttk.Separator(self.edit_form_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10)
        row += 1
        
        # 題名
        ttk.Label(self.edit_form_frame, text="題名:*", 
                 font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=5)
        self.edit_title = ttk.Entry(self.edit_form_frame, width=50)
        self.edit_title.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 題名(英)
        ttk.Label(self.edit_form_frame, text="題名(英):").grid(
            row=row, column=0, sticky="w", pady=5)
        self.edit_title_en = ttk.Entry(self.edit_form_frame, width=50)
        self.edit_title_en.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 著者
        ttk.Label(self.edit_form_frame, text="著者:*", 
                 font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=5)
        self.edit_authors = ttk.Entry(self.edit_form_frame, width=50)
        self.edit_authors.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 著者(英)
        ttk.Label(self.edit_form_frame, text="著者(英):").grid(
            row=row, column=0, sticky="w", pady=5)
        self.edit_authors_en = ttk.Entry(self.edit_form_frame, width=50)
        self.edit_authors_en.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 年
        ttk.Label(self.edit_form_frame, text="発表年:*", 
                 font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=5)
        self.edit_year = ttk.Entry(self.edit_form_frame, width=50)
        self.edit_year.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # タグ
        ttk.Label(self.edit_form_frame, text="タグ:").grid(
            row=row, column=0, sticky="w", pady=5)
        self.edit_tags = ttk.Entry(self.edit_form_frame, width=50)
        self.edit_tags.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 元ファイル
        ttk.Label(self.edit_form_frame, text="元ファイル:").grid(
            row=row, column=0, sticky="w", pady=5)
        self.edit_original_file = ttk.Entry(self.edit_form_frame, width=50)
        self.edit_original_file.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 要約
        ttk.Label(self.edit_form_frame, text="要約:").grid(
            row=row, column=0, sticky="nw", pady=5)
        self.edit_summary = scrolledtext.ScrolledText(
            self.edit_form_frame, width=50, height=6, wrap=tk.WORD)
        self.edit_summary.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        # 本文
        ttk.Label(self.edit_form_frame, text="本文:").grid(
            row=row, column=0, sticky="nw", pady=5)
        self.edit_fulltext = scrolledtext.ScrolledText(
            self.edit_form_frame, width=50, height=12, wrap=tk.WORD)
        self.edit_fulltext.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1
        
        self.edit_form_frame.columnconfigure(1, weight=1)
        
        # ボタンエリア
        button_frame = ttk.Frame(self.edit_form_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="💾 更新保存", 
                  command=self._update_paper, 
                  width=15).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="🗑️ 削除", 
                  command=self._delete_paper, 
                  width=15).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="🔄 クリア", 
                  command=self._clear_edit_form, 
                  width=15).pack(side="left", padx=5)
        
        # マウスホイールでスクロール
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # 初期データ読み込み
        self._refresh_edit_list()
        self._clear_edit_form()
    
    def _init_range_search_tab(self):
        """範囲検索タブ初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.tab_range_search)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 上部: 検索条件エリア
        search_frame = ttk.LabelFrame(main_frame, text="検索条件", padding=15)
        search_frame.pack(fill="x", pady=(0, 10))
        
        # 検索条件入力
        row = 0
        
        # 題名
        ttk.Label(search_frame, text="題名:").grid(
            row=row, column=0, sticky="w", pady=5, padx=(0, 10))
        self.range_title = ttk.Entry(search_frame, width=40)
        self.range_title.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(search_frame, text="(部分一致)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row, column=2, sticky="w", padx=(5, 0))
        row += 1
        
        # 著者
        ttk.Label(search_frame, text="著者:").grid(
            row=row, column=0, sticky="w", pady=5, padx=(0, 10))
        self.range_authors = ttk.Entry(search_frame, width=40)
        self.range_authors.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(search_frame, text="(部分一致)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row, column=2, sticky="w", padx=(5, 0))
        row += 1
        
        # 年（範囲指定）
        ttk.Label(search_frame, text="発表年:").grid(
            row=row, column=0, sticky="w", pady=5, padx=(0, 10))
        
        year_frame = ttk.Frame(search_frame)
        year_frame.grid(row=row, column=1, sticky="ew", pady=5)
        
        self.range_year_from = ttk.Entry(year_frame, width=10)
        self.range_year_from.pack(side="left")
        
        ttk.Label(year_frame, text=" 〜 ").pack(side="left", padx=5)
        
        self.range_year_to = ttk.Entry(year_frame, width=10)
        self.range_year_to.pack(side="left")
        
        ttk.Label(search_frame, text="(範囲指定)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row, column=2, sticky="w", padx=(5, 0))
        row += 1
        
        # タグ
        ttk.Label(search_frame, text="タグ:").grid(
            row=row, column=0, sticky="w", pady=5, padx=(0, 10))
        self.range_tags = ttk.Entry(search_frame, width=40)
        self.range_tags.grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Label(search_frame, text="(部分一致)", 
                 font=('Arial', 8), foreground='gray').grid(
            row=row, column=2, sticky="w", padx=(5, 0))
        row += 1
        
        search_frame.columnconfigure(1, weight=1)
        
        # ボタンエリア
        button_frame = ttk.Frame(search_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=15)
        
        ttk.Button(button_frame, text="🔍 検索実行", 
                  command=self._execute_range_search, 
                  width=15).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="🔄 条件クリア", 
                  command=self._clear_range_search, 
                  width=15).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="📋 全件表示", 
                  command=self._show_all_range, 
                  width=15).pack(side="left", padx=5)
        
        # 下部: 検索結果エリア
        result_frame = ttk.LabelFrame(main_frame, text="検索結果", padding=15)
        result_frame.pack(fill="both", expand=True)
        
        # ツールバー
        toolbar = ttk.Frame(result_frame)
        toolbar.pack(fill="x", pady=(0, 10))
        
        self.range_result_label = ttk.Label(toolbar, text="0 件", 
                                            foreground='gray')
        self.range_result_label.pack(side="left")
        
        ttk.Button(toolbar, text="📄 詳細表示", 
                  command=self._show_range_detail).pack(side="right", padx=5)
        
        # 結果テーブル
        table_frame = ttk.Frame(result_frame)
        table_frame.pack(fill="both", expand=True)
        
        # スクロールバー
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # Treeview作成
        columns = ('id', 'title', 'authors', 'year', 'tags')
        self.range_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # カラム設定
        self.range_tree.heading('id', text='ID')
        self.range_tree.heading('title', text='題名')
        self.range_tree.heading('authors', text='著者')
        self.range_tree.heading('year', text='年')
        self.range_tree.heading('tags', text='タグ')
        
        self.range_tree.column('id', width=50, anchor='center')
        self.range_tree.column('title', width=350, anchor='w')
        self.range_tree.column('authors', width=200, anchor='w')
        self.range_tree.column('year', width=80, anchor='center')
        self.range_tree.column('tags', width=250, anchor='w')
        
        y_scrollbar.config(command=self.range_tree.yview)
        x_scrollbar.config(command=self.range_tree.xview)
        
        self.range_tree.pack(fill="both", expand=True)
        
        # ダブルクリックで詳細表示
        self.range_tree.bind('<Double-1>', lambda e: self._show_range_detail())
        
        # Enterキーで検索実行
        self.range_title.bind('<Return>', lambda e: self._execute_range_search())
        self.range_authors.bind('<Return>', lambda e: self._execute_range_search())
        self.range_year_from.bind('<Return>', lambda e: self._execute_range_search())
        self.range_year_to.bind('<Return>', lambda e: self._execute_range_search())
        self.range_tags.bind('<Return>', lambda e: self._execute_range_search())
    
    def _init_fulltext_search_tab(self):
        """全文検索タブ初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.tab_fulltext_search)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 上部: 検索エリア
        search_frame = ttk.LabelFrame(main_frame, text="全文検索", padding=15)
        search_frame.pack(fill="x", pady=(0, 10))
        
        # 検索キーワード入力
        search_input_frame = ttk.Frame(search_frame)
        search_input_frame.pack(fill="x", pady=10)
        
        ttk.Label(search_input_frame, text="キーワード:", 
                 font=('Arial', 10, 'bold')).pack(side="left", padx=(0, 10))
        
        self.fulltext_keyword = ttk.Entry(search_input_frame, width=50, 
                                         font=('Arial', 11))
        self.fulltext_keyword.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        ttk.Button(search_input_frame, text="🔍 検索", 
                  command=self._execute_fulltext_search, 
                  width=12).pack(side="left", padx=5)
        
        ttk.Button(search_input_frame, text="🔄 クリア", 
                  command=self._clear_fulltext_search, 
                  width=12).pack(side="left")
        
        # 検索オプション
        option_frame = ttk.Frame(search_frame)
        option_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(option_frame, text="検索対象:", 
                 font=('Arial', 9)).pack(side="left", padx=(0, 10))
        
        self.fulltext_search_summary = tk.BooleanVar(value=True)
        ttk.Checkbutton(option_frame, text="要約", 
                       variable=self.fulltext_search_summary).pack(side="left", padx=5)
        
        self.fulltext_search_content = tk.BooleanVar(value=True)
        ttk.Checkbutton(option_frame, text="本文", 
                       variable=self.fulltext_search_content).pack(side="left", padx=5)
        
        # ヘルプテキスト
        help_label = ttk.Label(
            search_frame, 
            text="💡 要約や本文に含まれるキーワードを検索します。部分一致で検索されます。",
            font=('Arial', 9),
            foreground='gray'
        )
        help_label.pack(fill="x", pady=(5, 0))
        
        # 下部: 検索結果エリア
        result_frame = ttk.LabelFrame(main_frame, text="検索結果", padding=15)
        result_frame.pack(fill="both", expand=True)
        
        # ツールバー
        toolbar = ttk.Frame(result_frame)
        toolbar.pack(fill="x", pady=(0, 10))
        
        self.fulltext_result_label = ttk.Label(toolbar, text="0 件", 
                                               foreground='gray')
        self.fulltext_result_label.pack(side="left")
        
        ttk.Button(toolbar, text="📄 詳細表示", 
                  command=self._show_fulltext_detail).pack(side="right", padx=5)
        
        ttk.Button(toolbar, text="📋 プレビュー", 
                  command=self._show_fulltext_preview).pack(side="right", padx=5)
        
        # 結果テーブル
        table_frame = ttk.Frame(result_frame)
        table_frame.pack(fill="both", expand=True)
        
        # スクロールバー
        y_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal")
        x_scrollbar.pack(side="bottom", fill="x")
        
        # Treeview作成
        columns = ('id', 'title', 'authors', 'year', 'match_info')
        self.fulltext_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set
        )
        
        # カラム設定
        self.fulltext_tree.heading('id', text='ID')
        self.fulltext_tree.heading('title', text='題名')
        self.fulltext_tree.heading('authors', text='著者')
        self.fulltext_tree.heading('year', text='年')
        self.fulltext_tree.heading('match_info', text='マッチ箇所')
        
        self.fulltext_tree.column('id', width=50, anchor='center')
        self.fulltext_tree.column('title', width=300, anchor='w')
        self.fulltext_tree.column('authors', width=180, anchor='w')
        self.fulltext_tree.column('year', width=70, anchor='center')
        self.fulltext_tree.column('match_info', width=300, anchor='w')
        
        y_scrollbar.config(command=self.fulltext_tree.yview)
        x_scrollbar.config(command=self.fulltext_tree.xview)
        
        self.fulltext_tree.pack(fill="both", expand=True)
        
        # ダブルクリックで詳細表示
        self.fulltext_tree.bind('<Double-1>', lambda e: self._show_fulltext_detail())
        
        # Enterキーで検索実行
        self.fulltext_keyword.bind('<Return>', lambda e: self._execute_fulltext_search())
        
        # フォーカス設定
        self.fulltext_keyword.focus()
    
    # ================================
    # メニュー機能
    # ================================
    
    def _backup_database(self):
        """データベースバックアップ"""
        import shutil
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'papers_backup_{timestamp}.db'
        
        try:
            shutil.copy2('papers.db', backup_file)
            messagebox.showinfo("バックアップ完了", 
                              f"バックアップを作成しました:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("エラー", f"バックアップに失敗しました:\n{str(e)}")
    
    def _export_csv(self):
        """CSV出力"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            papers = self.db.get_all_papers()
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', '題名', '題名(英)', '著者', '著者(英)', 
                               '年', 'タグ', '要約', '作成日時', '更新日時'])
                for paper in papers:
                    writer.writerow([
                        paper[0], paper[1], paper[2], paper[3], paper[4],
                        paper[5], paper[6], paper[7], paper[10], paper[11]
                    ])
            messagebox.showinfo("エクスポート完了", 
                              f"CSVファイルを保存しました:\n{file_path}")
        except Exception as e:
            messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{str(e)}")
    
    def _show_help(self):
        """ヘルプ表示"""
        help_text = """
【学術論文管理システム 使い方】

■ 論文登録タブ
・論文情報を入力してデータベースに登録します
・テキストファイルから本文を読み込むことができます

■ 一覧表示タブ
・登録されている全論文を一覧表示します

■ 編集・削除タブ
・既存の論文データを編集・削除します

■ 範囲検索タブ
・題名、著者、年、タグで絞り込み検索します

■ 全文検索タブ
・要約や本文からキーワード検索します
        """
        messagebox.showinfo("使い方", help_text)
    
    def _show_about(self):
        """バージョン情報表示"""
        messagebox.showinfo("バージョン情報", 
                          "学術論文管理システム v1.0\n\n"
                          "論文の題名、著者、年、タグ、要約、本文を\n"
                          "管理・検索するアプリケーションです。")
    
    def on_closing(self):
        """アプリケーション終了処理"""
        if messagebox.askokcancel("終了確認", "アプリケーションを終了しますか?"):
            self.destroy()
    
    # ================================
    # 論文登録タブ関連メソッド
    # ================================
    
    def _browse_file(self):
        """ファイル選択ダイアログ"""
        file_path = filedialog.askopenfilename(
            title="テキストファイルを選択",
            filetypes=[
                ("テキストファイル", "*.txt"),
                ("全てのファイル", "*.*")
            ]
        )
        if file_path:
            self.input_file_path.delete(0, tk.END)
            self.input_file_path.insert(0, file_path)
    
    def _load_file(self):
        """ファイル読み込み"""
        file_path = self.input_file_path.get().strip()
        
        if not file_path:
            messagebox.showwarning("警告", "ファイルパスを入力してください。")
            return
        
        if not os.path.exists(file_path):
            messagebox.showerror("エラー", "指定されたファイルが見つかりません。")
            return
        
        try:
            # まずUTF-8で試す
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # UTF-8で失敗したらShift_JISで試す
                with open(file_path, 'r', encoding='shift_jis') as f:
                    content = f.read()
            
            # 本文エリアに表示
            self.input_fulltext.delete('1.0', tk.END)
            self.input_fulltext.insert('1.0', content)
            
            messagebox.showinfo("成功", 
                              f"ファイルを読み込みました。\n文字数: {len(content)} 文字")
            
        except Exception as e:
            messagebox.showerror("エラー", 
                               f"ファイルの読み込みに失敗しました:\n{str(e)}")
    
    def _update_char_count(self, event=None):
        """文字数カウント更新"""
        try:
            content = self.input_fulltext.get('1.0', tk.END)
            char_count = len(content.strip())
            self.char_count_label.config(text=f"{char_count:,} 文字")
            # Modified フラグをリセット
            self.input_fulltext.edit_modified(False)
        except:
            pass
    
    def _save_paper(self):
        """論文データ保存"""
        # 入力値取得
        title = self.input_title.get().strip()
        title_en = self.input_title_en.get().strip()
        authors = self.input_authors.get().strip()
        authors_en = self.input_authors_en.get().strip()
        year_str = self.input_year.get().strip()
        tags = self.input_tags.get().strip()
        summary = self.input_summary.get('1.0', tk.END).strip()
        fulltext = self.input_fulltext.get('1.0', tk.END).strip()
        original_file = self.input_file_path.get().strip()
        
        # 必須項目チェック
        if not title:
            messagebox.showwarning("入力エラー", "題名を入力してください。")
            self.input_title.focus()
            return
        
        if not authors:
            messagebox.showwarning("入力エラー", "著者を入力してください。")
            self.input_authors.focus()
            return
        
        if not year_str:
            messagebox.showwarning("入力エラー", "発表年を入力してください。")
            self.input_year.focus()
            return
        
        # 年の妥当性チェック
        try:
            year = int(year_str)
            if year < 1000 or year > 9999:
                raise ValueError
        except ValueError:
            messagebox.showwarning("入力エラー", 
                                 "発表年は1000〜9999の整数で入力してください。")
            self.input_year.focus()
            return
        
        # データベースに保存
        try:
            paper_id = self.db.add_paper(
                title=title,
                title_en=title_en if title_en else title,
                authors=authors,
                authors_en=authors_en if authors_en else authors,
                year=year,
                tags=tags,
                summary=summary,
                fulltext=fulltext,
                original_file=original_file
            )
            
            messagebox.showinfo("保存完了", 
                              f"論文データを保存しました。(ID: {paper_id})")
            
            # フォームクリア
            self._clear_input_form()
            
        except Exception as e:
            messagebox.showerror("エラー", 
                               f"保存に失敗しました:\n{str(e)}")
    
    def _clear_input_form(self):
        """入力フォームクリア"""
        self.input_title.delete(0, tk.END)
        self.input_title_en.delete(0, tk.END)
        self.input_authors.delete(0, tk.END)
        self.input_authors_en.delete(0, tk.END)
        self.input_year.delete(0, tk.END)
        self.input_tags.delete(0, tk.END)
        self.input_file_path.delete(0, tk.END)
        self.input_summary.delete('1.0', tk.END)
        self.input_fulltext.delete('1.0', tk.END)
        self.char_count_label.config(text="0 文字")
    
    # ================================
    # 一覧表示タブ関連メソッド
    # ================================
    
    def _refresh_list(self):
        """一覧更新"""
        # 既存データクリア
        for item in self.list_tree.get_children():
            self.list_tree.delete(item)
        
        # データベースから全論文取得
        papers = self.db.get_all_papers()
        
        # テーブルに追加
        for paper in papers:
            paper_id = paper[0]
            title = paper[1]
            authors = paper[3]
            year = paper[5]
            tags = paper[6]
            created_at = paper[10]
            
            # タグが長い場合は省略
            if tags and len(tags) > 30:
                tags = tags[:27] + "..."
            
            self.list_tree.insert('', 'end', values=(
                paper_id, title, authors, year, tags, created_at
            ))
        
        # 件数表示
        count = len(papers)
        self.list_count_label.config(text=f"{count} 件")
    
    def _show_paper_detail(self):
        """論文詳細表示"""
        # 選択されている行を取得
        selection = self.list_tree.selection()
        
        if not selection:
            messagebox.showwarning("警告", "論文を選択してください。")
            return
        
        # 最初の選択項目のIDを取得
        item = self.list_tree.item(selection[0])
        paper_id = item['values'][0]
        
        # データベースから論文情報取得
        paper = self.db.get_paper_by_id(paper_id)
        
        if not paper:
            messagebox.showerror("エラー", "論文データが見つかりません。")
            return
        
        # 詳細ウィンドウ作成
        detail_window = tk.Toplevel(self)
        detail_window.title(f"論文詳細 - ID: {paper_id}")
        detail_window.geometry("900x700")
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(detail_window)
        scrollbar = ttk.Scrollbar(detail_window, orient="vertical", 
                                  command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 詳細情報表示
        detail_frame = ttk.Frame(scrollable_frame, padding=20)
        detail_frame.pack(fill="both", expand=True)
        
        # 各フィールド表示
        self._add_detail_field(detail_frame, "ID:", str(paper[0]), 0)
        self._add_detail_field(detail_frame, "題名:", paper[1], 1)
        self._add_detail_field(detail_frame, "題名(英):", paper[2], 2)
        self._add_detail_field(detail_frame, "著者:", paper[3], 3)
        self._add_detail_field(detail_frame, "著者(英):", paper[4], 4)
        self._add_detail_field(detail_frame, "発表年:", str(paper[5]), 5)
        self._add_detail_field(detail_frame, "タグ:", paper[6], 6)
        
        # 要約
        ttk.Label(detail_frame, text="要約:", 
                 font=('Arial', 10, 'bold')).grid(
            row=7, column=0, sticky="nw", pady=10)
        
        summary_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, height=8, width=80)
        summary_text.grid(row=7, column=1, sticky="ew", pady=10)
        summary_text.insert('1.0', paper[7] if paper[7] else "")
        summary_text.config(state='disabled')
        
        # 本文
        ttk.Label(detail_frame, text="本文:", 
                 font=('Arial', 10, 'bold')).grid(
            row=8, column=0, sticky="nw", pady=10)
        
        fulltext_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, height=15, width=80)
        fulltext_text.grid(row=8, column=1, sticky="ew", pady=10)
        fulltext_text.insert('1.0', paper[8] if paper[8] else "")
        fulltext_text.config(state='disabled')
        
        # 元ファイル名
        self._add_detail_field(detail_frame, "元ファイル:", 
                              paper[9] if paper[9] else "", 9)
        
        # 登録・更新日時
        self._add_detail_field(detail_frame, "登録日時:", paper[10], 10)
        self._add_detail_field(detail_frame, "更新日時:", paper[11], 11)
        
        detail_frame.columnconfigure(1, weight=1)
        
        # ボタン
        button_frame = ttk.Frame(detail_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="閉じる", 
                  command=detail_window.destroy).pack()
        
        # スクロール設定
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # マウスホイールでスクロール
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        detail_window.protocol("WM_DELETE_WINDOW", 
                              lambda: [canvas.unbind_all("<MouseWheel>"), 
                                      detail_window.destroy()])
    
    # ================================
    # 全文検索タブ関連メソッド
    # ================================
    
    def _execute_fulltext_search(self):
        """全文検索実行"""
        keyword = self.fulltext_keyword.get().strip()
        
        if not keyword:
            messagebox.showwarning("入力エラー", "検索キーワードを入力してください。")
            self.fulltext_keyword.focus()
            return
        
        # 検索対象チェック
        search_summary = self.fulltext_search_summary.get()
        search_content = self.fulltext_search_content.get()
        
        if not search_summary and not search_content:
            messagebox.showwarning("検索オプション", 
                                 "検索対象（要約または本文）を選択してください。")
            return
        
        # 検索実行
        try:
            # データベースから全文検索
            papers = self.db.fulltext_search(keyword)
            
            # 検索対象でフィルタリング
            filtered_papers = []
            for paper in papers:
                summary = paper[7] if paper[7] else ""
                fulltext = paper[8] if paper[8] else ""
                
                # 検索対象に応じてフィルタ
                include = False
                if search_summary and keyword.lower() in summary.lower():
                    include = True
                if search_content and keyword.lower() in fulltext.lower():
                    include = True
                
                if include:
                    filtered_papers.append(paper)
            
            # 結果表示
            self._display_fulltext_results(filtered_papers, keyword)
            
        except Exception as e:
            messagebox.showerror("エラー", 
                               f"検索に失敗しました:\n{str(e)}")
    
    def _display_fulltext_results(self, papers, keyword):
        """全文検索結果表示"""
        # 既存データクリア
        for item in self.fulltext_tree.get_children():
            self.fulltext_tree.delete(item)
        
        # テーブルに追加
        for paper in papers:
            paper_id = paper[0]
            title = paper[1]
            authors = paper[3]
            year = paper[5]
            summary = paper[7] if paper[7] else ""
            fulltext = paper[8] if paper[8] else ""
            
            # マッチ箇所を特定
            match_info = []
            
            if keyword.lower() in summary.lower():
                # 要約内のマッチ箇所を抽出（前後30文字）
                match_pos = summary.lower().find(keyword.lower())
                start = max(0, match_pos - 30)
                end = min(len(summary), match_pos + len(keyword) + 30)
                snippet = summary[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(summary):
                    snippet = snippet + "..."
                match_info.append(f"[要約] {snippet}")
            
            if keyword.lower() in fulltext.lower():
                # 本文内のマッチ箇所を抽出（前後30文字）
                match_pos = fulltext.lower().find(keyword.lower())
                start = max(0, match_pos - 30)
                end = min(len(fulltext), match_pos + len(keyword) + 30)
                snippet = fulltext[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(fulltext):
                    snippet = snippet + "..."
                match_info.append(f"[本文] {snippet}")
            
            # マッチ情報を結合（最初の1つのみ表示）
            match_text = match_info[0] if match_info else ""
            
            self.fulltext_tree.insert('', 'end', values=(
                paper_id, title, authors, year, match_text
            ))
        
        # 件数表示
        count = len(papers)
        self.fulltext_result_label.config(
            text=f"{count} 件 (キーワード: {keyword})")
    
    def _clear_fulltext_search(self):
        """全文検索クリア"""
        self.fulltext_keyword.delete(0, tk.END)
        
        # 結果クリア
        for item in self.fulltext_tree.get_children():
            self.fulltext_tree.delete(item)
        
        self.fulltext_result_label.config(text="0 件")
        self.fulltext_keyword.focus()
    
    def _show_fulltext_detail(self):
        """全文検索結果から詳細表示"""
        # 選択されている行を取得
        selection = self.fulltext_tree.selection()
        
        if not selection:
            messagebox.showwarning("警告", "論文を選択してください。")
            return
        
        # 最初の選択項目のIDを取得
        item = self.fulltext_tree.item(selection[0])
        paper_id = item['values'][0]
        
        # データベースから論文情報取得
        paper = self.db.get_paper_by_id(paper_id)
        
        if not paper:
            messagebox.showerror("エラー", "論文データが見つかりません。")
            return
        
        # 詳細ウィンドウ作成
        self._show_paper_detail_window(paper)
    
    def _show_fulltext_preview(self):
        """マッチ箇所プレビュー表示"""
        # 選択されている行を取得
        selection = self.fulltext_tree.selection()
        
        if not selection:
            messagebox.showwarning("警告", "論文を選択してください。")
            return
        
        # 最初の選択項目のIDを取得
        item = self.fulltext_tree.item(selection[0])
        paper_id = item['values'][0]
        
        # データベースから論文情報取得
        paper = self.db.get_paper_by_id(paper_id)
        
        if not paper:
            messagebox.showerror("エラー", "論文データが見つかりません。")
            return
        
        keyword = self.fulltext_keyword.get().strip()
        
        # プレビューウィンドウ作成
        preview_window = tk.Toplevel(self)
        preview_window.title(f"マッチ箇所プレビュー - ID: {paper_id}")
        preview_window.geometry("800x600")
        
        # メインフレーム
        main_frame = ttk.Frame(preview_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # タイトル表示
        title_label = ttk.Label(main_frame, text=paper[1], 
                               font=('Arial', 12, 'bold'), 
                               wraplength=750)
        title_label.pack(fill="x", pady=(0, 10))
        
        # 著者・年表示
        info_label = ttk.Label(main_frame, 
                              text=f"{paper[3]} ({paper[5]})", 
                              font=('Arial', 10), 
                              foreground='gray')
        info_label.pack(fill="x", pady=(0, 20))
        
        # タブ作成
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        # 要約タブ
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="要約")
        
        summary_text = scrolledtext.ScrolledText(
            summary_frame, wrap=tk.WORD, font=('Arial', 10))
        summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        summary = paper[7] if paper[7] else ""
        if summary:
            summary_text.insert('1.0', summary)
            # キーワードをハイライト（簡易版）
            self._highlight_keyword(summary_text, keyword)
        else:
            summary_text.insert('1.0', "要約データがありません。")
        
        summary_text.config(state='disabled')
        
        # 本文タブ
        fulltext_frame = ttk.Frame(notebook)
        notebook.add(fulltext_frame, text="本文")
        
        fulltext_text = scrolledtext.ScrolledText(
            fulltext_frame, wrap=tk.WORD, font=('Arial', 10))
        fulltext_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        fulltext = paper[8] if paper[8] else ""
        if fulltext:
            fulltext_text.insert('1.0', fulltext)
            # キーワードをハイライト（簡易版）
            self._highlight_keyword(fulltext_text, keyword)
        else:
            fulltext_text.insert('1.0', "本文データがありません。")
        
        fulltext_text.config(state='disabled')
        
        # 閉じるボタン
        ttk.Button(main_frame, text="閉じる", 
                  command=preview_window.destroy).pack(pady=(10, 0))
    
    def _highlight_keyword(self, text_widget, keyword):
        """テキストウィジェット内のキーワードをハイライト"""
        # ハイライト用のタグ設定
        text_widget.tag_configure("highlight", background="yellow", 
                                 foreground="black")
        
        # テキスト取得
        content = text_widget.get('1.0', tk.END)
        
        # キーワードの位置を検索してハイライト
        start_pos = '1.0'
        while True:
            start_pos = text_widget.search(keyword, start_pos, 
                                          stopindex=tk.END, nocase=True)
            if not start_pos:
                break
            
            end_pos = f"{start_pos}+{len(keyword)}c"
            text_widget.tag_add("highlight", start_pos, end_pos)
            start_pos = end_pos
    
    def _add_detail_field(self, parent, label_text, value, row):
        """詳細フィールド追加ヘルパー"""
        ttk.Label(parent, text=label_text, 
                 font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky="w", pady=5, padx=(0, 10))
        
        value_label = ttk.Label(parent, text=value if value else "―", 
                               wraplength=600)
        value_label.grid(row=row, column=1, sticky="w", pady=5)
    
    # ================================
    # 編集・削除タブ関連メソッド
    # ================================
    
    def _refresh_edit_list(self):
        """編集用リスト更新"""
        
        # 1. リストクリア
        self.edit_listbox.delete(0, tk.END)
        
        # 2. データベースから全論文取得
        papers = self.db.get_all_papers()
        
        # 3. 【修正】IDを順番に管理するためのリストを初期化
        #    リストの構築ループの前に一度だけ実行します。
        self.edit_paper_ids = []
        
        # 4. リストに追加（ID, 年, 題名の形式）
        for paper in papers:
            paper_id = paper[0]
            title = paper[1]
            year = paper[5]
            display_text = f"[{paper_id}] {year} - {title[:50]}"
            if len(title) > 50:
                display_text += "..."
            
            self.edit_listbox.insert(tk.END, display_text)
            
            # IDをデータとして保持
            # 【修正点】itemconfigの代わりに、PythonリストへIDを追加
            # self.edit_listbox.itemconfig(tk.END, {'data': paper_id}) ← 削除
            self.edit_paper_ids.append(paper_id)
        
        # 5. 件数表示
        count = len(papers)
        self.edit_count_label.config(text=f"{count} 件")
        
        # 6. データをインスタンス変数として保存（後で参照用）
        self.edit_papers_data = {paper[0]: paper for paper in papers}
        
    def _on_edit_select(self, event):
        """リストボックス選択時"""
        selection = self.edit_listbox.curselection()
        
        if not selection:
            return
        
        # 選択されたテキストからIDを抽出
        selected_text = self.edit_listbox.get(selection[0])
        paper_id = int(selected_text.split(']')[0].replace('[', ''))
        
        # データベースから論文情報取得
        paper = self.db.get_paper_by_id(paper_id)
        
        if not paper:
            messagebox.showerror("エラー", "論文データが見つかりません。")
            return
        
        # フォームに反映
        self._load_paper_to_edit_form(paper)
    
    def _load_paper_to_edit_form(self, paper):
        """論文データをフォームに読み込み"""
        # フォームクリア
        self._clear_edit_form()
        
        # 各フィールドに設定
        self.edit_id_label.config(text=str(paper[0]))
        
        self.edit_title.insert(0, paper[1] if paper[1] else "")
        self.edit_title_en.insert(0, paper[2] if paper[2] else "")
        self.edit_authors.insert(0, paper[3] if paper[3] else "")
        self.edit_authors_en.insert(0, paper[4] if paper[4] else "")
        self.edit_year.insert(0, str(paper[5]) if paper[5] else "")
        self.edit_tags.insert(0, paper[6] if paper[6] else "")
        self.edit_original_file.insert(0, paper[9] if paper[9] else "")
        
        self.edit_summary.insert('1.0', paper[7] if paper[7] else "")
        self.edit_fulltext.insert('1.0', paper[8] if paper[8] else "")
    
    def _clear_edit_form(self):
        """編集フォームクリア"""
        self.edit_id_label.config(text="―")
        
        self.edit_title.delete(0, tk.END)
        self.edit_title_en.delete(0, tk.END)
        self.edit_authors.delete(0, tk.END)
        self.edit_authors_en.delete(0, tk.END)
        self.edit_year.delete(0, tk.END)
        self.edit_tags.delete(0, tk.END)
        self.edit_original_file.delete(0, tk.END)
        
        self.edit_summary.delete('1.0', tk.END)
        self.edit_fulltext.delete('1.0', tk.END)
    
    def _update_paper(self):
        """論文データ更新"""
        # IDチェック
        paper_id_text = self.edit_id_label.cget("text")
        
        if paper_id_text == "―":
            messagebox.showwarning("警告", "編集する論文を選択してください。")
            return
        
        paper_id = int(paper_id_text)
        
        # 入力値取得
        title = self.edit_title.get().strip()
        title_en = self.edit_title_en.get().strip()
        authors = self.edit_authors.get().strip()
        authors_en = self.edit_authors_en.get().strip()
        year_str = self.edit_year.get().strip()
        tags = self.edit_tags.get().strip()
        original_file = self.edit_original_file.get().strip()
        summary = self.edit_summary.get('1.0', tk.END).strip()
        fulltext = self.edit_fulltext.get('1.0', tk.END).strip()
        
        # 必須項目チェック
        if not title:
            messagebox.showwarning("入力エラー", "題名を入力してください。")
            self.edit_title.focus()
            return
        
        if not authors:
            messagebox.showwarning("入力エラー", "著者を入力してください。")
            self.edit_authors.focus()
            return
        
        if not year_str:
            messagebox.showwarning("入力エラー", "発表年を入力してください。")
            self.edit_year.focus()
            return
        
        # 年の妥当性チェック
        try:
            year = int(year_str)
            if year < 1000 or year > 9999:
                raise ValueError
        except ValueError:
            messagebox.showwarning("入力エラー", 
                                 "発表年は1000〜9999の整数で入力してください。")
            self.edit_year.focus()
            return
        
        # 確認ダイアログ
        if not messagebox.askyokcancel("更新確認", 
                                       f"論文ID {paper_id} のデータを更新しますか?"):
            return
        
        # データベース更新
        try:
            self.db.update_paper(
                paper_id=paper_id,
                title=title,
                title_en=title_en if title_en else title,
                authors=authors,
                authors_en=authors_en if authors_en else authors,
                year=year,
                tags=tags,
                summary=summary,
                fulltext=fulltext,
                original_file=original_file
            )
            
            messagebox.showinfo("更新完了", 
                              f"論文ID {paper_id} のデータを更新しました。")
            
            # リスト更新
            self._refresh_edit_list()
            
            # 一覧タブも更新
            self._refresh_list()
            
        except Exception as e:
            messagebox.showerror("エラー", 
                               f"更新に失敗しました:\n{str(e)}")
    
    def _delete_paper(self):
        """論文データ削除"""
        # IDチェック
        paper_id_text = self.edit_id_label.cget("text")
        
        if paper_id_text == "―":
            messagebox.showwarning("警告", "削除する論文を選択してください。")
            return
        
        paper_id = int(paper_id_text)
        
        # 確認ダイアログ
        title = self.edit_title.get().strip()
        result = messagebox.askyesno(
            "削除確認",
            f"本当に削除しますか?\n\nID: {paper_id}\n題名: {title}\n\n"
            "この操作は取り消せません。"
        )
        
        if not result:
            return
        
        # データベースから削除
        try:
            self.db.delete_paper(paper_id)
            
            messagebox.showinfo("削除完了", 
                              f"論文ID {paper_id} を削除しました。")
            
            # フォームクリア
            self._clear_edit_form()
            
            # リスト更新
            self._refresh_edit_list()
            
            # 一覧タブも更新
            self._refresh_list()
            
        except Exception as e:
            messagebox.showerror("エラー", 
                               f"削除に失敗しました:\n{str(e)}")
    
    # ================================
    # 範囲検索タブ関連メソッド
    # ================================
    
    def _execute_range_search(self):
        """範囲検索実行"""
        # 検索条件取得
        title = self.range_title.get().strip()
        authors = self.range_authors.get().strip()
        year_from_str = self.range_year_from.get().strip()
        year_to_str = self.range_year_to.get().strip()
        tags = self.range_tags.get().strip()
        
        # 年の範囲チェック
        year_from = None
        year_to = None
        
        if year_from_str:
            try:
                year_from = int(year_from_str)
                if year_from < 1000 or year_from > 9999:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("入力エラー", 
                                     "開始年は1000〜9999の整数で入力してください。")
                self.range_year_from.focus()
                return
        
        if year_to_str:
            try:
                year_to = int(year_to_str)
                if year_to < 1000 or year_to > 9999:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("入力エラー", 
                                     "終了年は1000〜9999の整数で入力してください。")
                self.range_year_to.focus()
                return
        
        # 年の範囲妥当性チェック
        if year_from and year_to and year_from > year_to:
            messagebox.showwarning("入力エラー", 
                                 "開始年は終了年以下である必要があります。")
            self.range_year_from.focus()
            return
        
        # 検索実行
        try:
            papers = self.db.search_papers(
                title=title,
                authors=authors,
                year_from=year_from,
                year_to=year_to,
                tags=tags
            )
            
            # 結果表示
            self._display_range_results(papers)
            
        except Exception as e:
            messagebox.showerror("エラー", 
                               f"検索に失敗しました:\n{str(e)}")
    
    def _display_range_results(self, papers):
        """検索結果表示"""
        # 既存データクリア
        for item in self.range_tree.get_children():
            self.range_tree.delete(item)
        
        # テーブルに追加
        for paper in papers:
            paper_id = paper[0]
            title = paper[1]
            authors = paper[3]
            year = paper[5]
            tags = paper[6]
            
            # タグが長い場合は省略
            if tags and len(tags) > 40:
                tags = tags[:37] + "..."
            
            self.range_tree.insert('', 'end', values=(
                paper_id, title, authors, year, tags
            ))
        
        # 件数表示
        count = len(papers)
        self.range_result_label.config(text=f"{count} 件")
        
        # 検索条件表示（オプション）
        conditions = []
        if self.range_title.get().strip():
            conditions.append(f"題名: {self.range_title.get().strip()}")
        if self.range_authors.get().strip():
            conditions.append(f"著者: {self.range_authors.get().strip()}")
        if self.range_year_from.get().strip() or self.range_year_to.get().strip():
            year_cond = "年: "
            if self.range_year_from.get().strip():
                year_cond += self.range_year_from.get().strip()
            year_cond += "〜"
            if self.range_year_to.get().strip():
                year_cond += self.range_year_to.get().strip()
            conditions.append(year_cond)
        if self.range_tags.get().strip():
            conditions.append(f"タグ: {self.range_tags.get().strip()}")
        
        if conditions:
            cond_text = " | ".join(conditions)
            self.range_result_label.config(
                text=f"{count} 件 ({cond_text})")
        else:
            self.range_result_label.config(text=f"{count} 件 (全件)")
    
    def _clear_range_search(self):
        """検索条件クリア"""
        self.range_title.delete(0, tk.END)
        self.range_authors.delete(0, tk.END)
        self.range_year_from.delete(0, tk.END)
        self.range_year_to.delete(0, tk.END)
        self.range_tags.delete(0, tk.END)
        
        # 結果もクリア
        for item in self.range_tree.get_children():
            self.range_tree.delete(item)
        
        self.range_result_label.config(text="0 件")
    
    def _show_all_range(self):
        """全件表示"""
        # 検索条件クリア
        self.range_title.delete(0, tk.END)
        self.range_authors.delete(0, tk.END)
        self.range_year_from.delete(0, tk.END)
        self.range_year_to.delete(0, tk.END)
        self.range_tags.delete(0, tk.END)
        
        # 全件検索
        self._execute_range_search()
    
    def _show_range_detail(self):
        """範囲検索結果から詳細表示"""
        # 選択されている行を取得
        selection = self.range_tree.selection()
        
        if not selection:
            messagebox.showwarning("警告", "論文を選択してください。")
            return
        
        # 最初の選択項目のIDを取得
        item = self.range_tree.item(selection[0])
        paper_id = item['values'][0]
        
        # データベースから論文情報取得
        paper = self.db.get_paper_by_id(paper_id)
        
        if not paper:
            messagebox.showerror("エラー", "論文データが見つかりません。")
            return
        
        # 詳細ウィンドウ作成（一覧タブと同じロジック）
        self._show_paper_detail_window(paper)
    
    def _show_paper_detail_window(self, paper):
        """論文詳細ウィンドウ表示（共通）"""
        paper_id = paper[0]
        
        # 詳細ウィンドウ作成
        detail_window = tk.Toplevel(self)
        detail_window.title(f"論文詳細 - ID: {paper_id}")
        detail_window.geometry("900x700")
        
        # スクロール可能なフレーム
        canvas = tk.Canvas(detail_window)
        scrollbar = ttk.Scrollbar(detail_window, orient="vertical", 
                                  command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 詳細情報表示
        detail_frame = ttk.Frame(scrollable_frame, padding=20)
        detail_frame.pack(fill="both", expand=True)
        
        # 各フィールド表示
        self._add_detail_field(detail_frame, "ID:", str(paper[0]), 0)
        self._add_detail_field(detail_frame, "題名:", paper[1], 1)
        self._add_detail_field(detail_frame, "題名(英):", paper[2], 2)
        self._add_detail_field(detail_frame, "著者:", paper[3], 3)
        self._add_detail_field(detail_frame, "著者(英):", paper[4], 4)
        self._add_detail_field(detail_frame, "発表年:", str(paper[5]), 5)
        self._add_detail_field(detail_frame, "タグ:", paper[6], 6)
        
        # 要約
        ttk.Label(detail_frame, text="要約:", 
                 font=('Arial', 10, 'bold')).grid(
            row=7, column=0, sticky="nw", pady=10)
        
        summary_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, height=8, width=80)
        summary_text.grid(row=7, column=1, sticky="ew", pady=10)
        summary_text.insert('1.0', paper[7] if paper[7] else "")
        summary_text.config(state='disabled')
        
        # 本文
        ttk.Label(detail_frame, text="本文:", 
                 font=('Arial', 10, 'bold')).grid(
            row=8, column=0, sticky="nw", pady=10)
        
        fulltext_text = scrolledtext.ScrolledText(
            detail_frame, wrap=tk.WORD, height=15, width=80)
        fulltext_text.grid(row=8, column=1, sticky="ew", pady=10)
        fulltext_text.insert('1.0', paper[8] if paper[8] else "")
        fulltext_text.config(state='disabled')
        
        # 元ファイル名
        self._add_detail_field(detail_frame, "元ファイル:", 
                              paper[9] if paper[9] else "", 9)
        
        # 登録・更新日時
        self._add_detail_field(detail_frame, "登録日時:", paper[10], 10)
        self._add_detail_field(detail_frame, "更新日時:", paper[11], 11)
        
        detail_frame.columnconfigure(1, weight=1)
        
        # ボタン
        button_frame = ttk.Frame(detail_frame)
        button_frame.grid(row=12, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="閉じる", 
                  command=detail_window.destroy).pack()
        
        # スクロール設定
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # マウスホイールでスクロール
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        detail_window.protocol("WM_DELETE_WINDOW", 
                              lambda: [canvas.unbind_all("<MouseWheel>"), 
                                      detail_window.destroy()])


# ================================
# メイン処理
# ================================

if __name__ == "__main__":
    # データベース初期化
    init_db()
    
    # アプリケーション起動
    app = PaperManagerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()