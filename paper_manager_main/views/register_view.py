import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import pathlib
import importlib.util

# Robust import of the database layer to support both package import and direct script execution
PaperDatabase = None
try:
    from ..db import PaperDatabase
except Exception:
    base_dir = pathlib.Path(__file__).resolve().parents[1]  # paper_manager_main
    db_path = base_dir / "db.py"
    spec_db = importlib.util.spec_from_file_location("paper_manager_main.db", str(db_path))
    db_module = importlib.util.module_from_spec(spec_db)
    spec_db.loader.exec_module(db_module)
    PaperDatabase = getattr(db_module, "PaperDatabase", None)

class RegisterView(ttk.Frame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db or PaperDatabase()
        self._build_ui()

    def _build_ui(self):
        # Two-column layout: form (left) and本文プレビュー (右)
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.LabelFrame(main_frame, text="論文情報入力", padding=12)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        right_frame = ttk.LabelFrame(main_frame, text="本文プレビュー", padding=12)
        right_frame.grid(row=0, column=1, sticky="nsew")

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)

        # 入力項目
        row = 0
        ttk.Label(left_frame, text="題名:*").grid(row=row, column=0, sticky="w", pady=5)
        self.input_title = ttk.Entry(left_frame, width=40)
        self.input_title.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(left_frame, text="題名(英):").grid(row=row, column=0, sticky="w", pady=5)
        self.input_title_en = ttk.Entry(left_frame, width=40)
        self.input_title_en.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(left_frame, text="著者:*").grid(row=row, column=0, sticky="w", pady=5)
        self.input_authors = ttk.Entry(left_frame, width=40)
        self.input_authors.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(left_frame, text="著者(英):").grid(row=row, column=0, sticky="w", pady=5)
        self.input_authors_en = ttk.Entry(left_frame, width=40)
        self.input_authors_en.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(left_frame, text="発表年:*").grid(row=row, column=0, sticky="w", pady=5)
        self.input_year = ttk.Entry(left_frame, width=20)
        self.input_year.grid(row=row, column=1, sticky="w", pady=5)
        row += 1

        ttk.Label(left_frame, text="タグ:").grid(row=row, column=0, sticky="w", pady=5)
        self.input_tags = ttk.Entry(left_frame, width=40)
        self.input_tags.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Label(left_frame, text="要約:").grid(row=row, column=0, sticky="nw", pady=5)
        self.input_summary = scrolledtext.ScrolledText(left_frame, width=40, height=6, wrap=tk.WORD)
        self.input_summary.grid(row=row, column=1, sticky="ew", pady=5)
        row += 1

        ttk.Button(left_frame, text="💾 保存", command=self._save_paper, width=15).grid(row=row, column=0, columnspan=2, pady=10)

        # 本文プレビュー
        self.input_fulltext = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=60, height=20)
        self.input_fulltext.pack(fill="both", expand=True)

    def _save_paper(self):
        title = self.input_title.get().strip()
        title_en = self.input_title_en.get().strip()
        authors = self.input_authors.get().strip()
        authors_en = self.input_authors_en.get().strip()
        year_text = self.input_year.get().strip()
        tags = self.input_tags.get().strip()
        summary = self.input_summary.get('1.0', 'end').strip()
        fulltext = self.input_fulltext.get('1.0', 'end').strip()
        original_file = ""  # 将来拡張

        if not title or not authors or not year_text:
            messagebox.showwarning("入力エラー", "題名・著者・年は必須です。")
            return
        try:
            year = int(year_text)
        except ValueError:
            messagebox.showwarning("入力エラー", "発表年は数値で入力してください。")
            return

        paper_id = self.db.add_paper(
            title=title,
            title_en=title_en or None,
            authors=authors,
            authors_en=authors_en or None,
            year=year,
            tags=tags,
            summary=summary,
            fulltext=fulltext,
            original_file=original_file or None
        )
        messagebox.showinfo("保存完了", f"論文データを保存しました。(ID: {paper_id})")
        self._clear_inputs()

    def _clear_inputs(self):
        self.input_title.delete(0, tk.END)
        self.input_title_en.delete(0, tk.END)
        self.input_authors.delete(0, tk.END)
        self.input_authors_en.delete(0, tk.END)
        self.input_year.delete(0, tk.END)
        self.input_tags.delete(0, tk.END)
        self.input_summary.delete('1.0', tk.END)
        self.input_fulltext.delete('1.0', tk.END)


