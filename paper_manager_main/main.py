import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# 簡易インメモリデータストア（基アプリのDB連携が未実装の場合の代替案）
class InMemoryPaperStore:
    def __init__(self):
        self.papers = []

    def add_paper(self, title, authors, year, tags, summary, fulltext, original_file):
        paper_id = len(self.papers) + 1
        paper = {
            "id": paper_id,
            "title": title,
            "authors": authors,
            "year": year,
            "tags": tags,
            "summary": summary,
            "fulltext": fulltext,
            "original_file": original_file,
            "created_at": "",
            "updated_at": ""
        }
        self.papers.append(paper)
        return paper_id

    def get_all(self):
        return self.papers

class PaperManagerApp(tk.Tk):
    """
    基本的な左ナビ付きUIを再現する簡易版アプリ。
    - 左: ナビゲーション（ホーム/論文登録/論文一覧/検索/統計/設定）
    - 右: 各ページのコンテンツ領域
    - DB接続は現状インメモリストアで代替
    """
    def __init__(self):
        super().__init__()
        self.title("学術論文管理システム - Base風UI")
        self.geometry("1100x700")
        self.store = InMemoryPaperStore()
        self._setup_ui()

    def _setup_ui(self):
        # 左ナビ
        self.sidebar = ttk.Frame(self, width=220)
        self.sidebar.pack(side="left", fill="y")

        # コンテンツ領域
        self.content = ttk.Frame(self)
        self.content.pack(side="right", fill="both", expand=True)

        nav_items = [
            ("ホーム", "home"),
            ("論文一覧", "list"),
            ("論文登録", "register"),
            ("検索", "search"),
            ("統計", "stats"),
            ("設定", "settings"),
        ]
        self.frames = {}
        for label, key in nav_items:
            ttk.Button(self.sidebar, text=label, width=22, command=lambda k=key: self.show(k)).pack(pady=6)

        # 各ページの定義
        self.frames["home"] = ttk.Frame(self.content)
        ttk.Label(self.frames["home"], text="ようこそ", font=("Arial", 14)).pack(padx=20, pady=20)

        self.frames["list"] = ttk.Frame(self.content)
        self._init_list_page(self.frames["list"])

        self.frames["register"] = ttk.Frame(self.content)
        self._init_register_page(self.frames["register"])

        self.frames["search"] = ttk.Frame(self.content)
        self._init_search_page(self.frames["search"])

        self.frames["stats"] = ttk.Frame(self.content)
        self._init_stats_page(self.frames["stats"])

        self.frames["settings"] = ttk.Frame(self.content)
        self._init_settings_page(self.frames["settings"])

        for f in self.frames.values():
            f.place(relwidth=1, relheight=1)

        self.show("home")

    def show(self, name):
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()

    # ホームページはシンプルな案内
    def _init_home_content(self, frame):
        tk.Label(frame, text="基アプリ準拠のUIへ復元中...", font=("Arial", 12)).pack(padx=20, pady=20)

    # 論文登録ページ
    def _init_register_page(self, frame):
        self._init_home_content(frame)  # 既存の雰囲気を維持
        reg_frame = ttk.LabelFrame(frame, text="論文登録", padding=12)
        reg_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # 簡易フォーム
        ttk.Label(reg_frame, text="題名:").grid(row=0, column=0, sticky="w", pady=5)
        self.reg_title = ttk.Entry(reg_frame, width=60)
        self.reg_title.grid(row=0, column=1, sticky="ew", pady=5)

        ttk.Label(reg_frame, text="著者:").grid(row=1, column=0, sticky="w", pady=5)
        self.reg_authors = ttk.Entry(reg_frame, width=60)
        self.reg_authors.grid(row=1, column=1, sticky="ew", pady=5)

        ttk.Label(reg_frame, text="年:").grid(row=2, column=0, sticky="w", pady=5)
        self.reg_year = ttk.Entry(reg_frame, width=60)
        self.reg_year.grid(row=2, column=1, sticky="ew", pady=5)

        ttk.Label(reg_frame, text="タグ:").grid(row=3, column=0, sticky="w", pady=5)
        self.reg_tags = ttk.Entry(reg_frame, width=60)
        self.reg_tags.grid(row=3, column=1, sticky="ew", pady=5)

        ttk.Label(reg_frame, text="要約:").grid(row=4, column=0, sticky="nw", pady=5)
        self.reg_summary = tk.Text(reg_frame, height=6, width=60)
        self.reg_summary.grid(row=4, column=1, sticky="ew", pady=5)

        ttk.Label(reg_frame, text="本文:").grid(row=5, column=0, sticky="nw", pady=5)
        self.reg_fulltext = tk.Text(reg_frame, height=8, width=60)
        self.reg_fulltext.grid(row=5, column=1, sticky="ew", pady=5)

        reg_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(reg_frame, text="保存", command=self._handle_save_paper).grid(row=6, column=1, sticky="e", pady=10)

    def _handle_save_paper(self):
        title = self.reg_title.get().strip()
        authors = self.reg_authors.get().strip()
        year_text = self.reg_year.get().strip()
        tags = self.reg_tags.get().strip()
        summary = self.reg_summary.get("1.0", tk.END).strip()
        fulltext = self.reg_fulltext.get("1.0", tk.END).strip()

        if not title or not authors or not year_text:
            messagebox.showwarning("入力エラー", "題名・著者・年は必須です。")
            return
        try:
            year = int(year_text)
        except ValueError:
            messagebox.showwarning("入力エラー", "年は整数を入力してください。")
            return

        self.store.add_paper(title, authors, year, tags, summary, fulltext, "")
        messagebox.showinfo("保存完了", "論文を登録しました。")
        self.reg_title.delete(0, tk.END)
        self.reg_authors.delete(0, tk.END)
        self.reg_year.delete(0, tk.END)
        self.reg_tags.delete(0, tk.END)
        self.reg_summary.delete("1.0", tk.END)
        self.reg_fulltext.delete("1.0", tk.END)

        # 一覧ページを必要に応じて更新
        if "list" in self.frames:
            self._refresh_list_page(self.frames["list"])

    def _init_list_page(self, frame):
        self._init_home_content(frame)
        # 表示用のリスト
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self.paper_listbox = tk.Listbox(list_frame)
        self.paper_listbox.pack(side="left", fill="both", expand=True)
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.paper_listbox.yview)
        list_scroll.pack(side="right", fill="y")
        self.paper_listbox.config(yscrollcommand=list_scroll.set)
        self._refresh_list_page(frame)

    def _refresh_list_page(self, frame):
        if hasattr(self, "paper_listbox"):
            self.paper_listbox.delete(0, tk.END)
            for paper in self.store.get_all():
                display = f"{paper['id']}: {paper['title']} • {paper['authors']} ({paper['year']})"
                self.paper_listbox.insert(tk.END, display)

    def _init_search_page(self, frame):
        self._init_home_content(frame)
        search_frame = ttk.LabelFrame(frame, text="検索", padding=12)
        search_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(search_frame, text="キーワード:").grid(row=0, column=0, sticky="w", pady=5)
        self.search_input = ttk.Entry(search_frame, width=50)
        self.search_input.grid(row=0, column=1, sticky="w", pady=5)
        ttk.Button(search_frame, text="検索", command=self._perform_search).grid(row=0, column=2, padx=5)
        self.search_results = tk.Listbox(search_frame, height=10)
        self.search_results.grid(row=1, column=0, columnspan=3, sticky="nsew", pady=10)
        search_frame.grid_rowconfigure(1, weight=1)
        search_frame.grid_columnconfigure(1, weight=1)

    def _perform_search(self):
        keyword = self.search_input.get().strip().lower()
        self.search_results.delete(0, tk.END)
        for paper in self.store.get_all():
            if (keyword in (paper["title"] or "").lower()) or (keyword in (paper["authors"] or "").lower()):
                self.search_results.insert(tk.END, f'{paper["id"]}: {paper["title"]} - {paper["authors"]} ({paper["year"]})')

    def _init_stats_page(self, frame):
        self._init_home_content(frame)
        # ダミーの統計表示
        stats_frame = ttk.LabelFrame(frame, text="統計", padding=12)
        stats_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(stats_frame, text="登録論文数: 0", font=("Arial", 12)).pack(anchor="w", pady=5)
        ttk.Label(stats_frame, text="キーワード分析: 未実装", font=("Arial", 12)).pack(anchor="w", pady=5)

    def _init_settings_page(self, frame):
        self._init_home_content(frame)
        settings_frame = ttk.LabelFrame(frame, text="設定", padding=12)
        settings_frame.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(settings_frame, text="設定は現在ダミーです。", font=("Arial", 12)).pack(anchor="w", pady=5)

if __name__ == "__main__":
    # ベースUIとして新規実装を起動
    app = PaperManagerApp()
    app.mainloop()


