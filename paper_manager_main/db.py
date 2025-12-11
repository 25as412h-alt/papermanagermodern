import sqlite3
from datetime import datetime
from typing import Optional

DB_NAME = 'papers.db'

class PaperDatabase:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS papers (
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
            )''')
            conn.commit()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def add_paper(self, title, title_en, authors, authors_en, year, tags, summary, fulltext, original_file):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO papers 
                (title, title_en, authors, authors_en, year, tags, 
                 summary, fulltext, original_file, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (title, title_en, authors, authors_en, year, tags, summary, fulltext, original_file, now, now))
            paper_id = cursor.lastrowid
            conn.commit()
        return paper_id

    def get_paper(self, paper_id: int) -> Optional[tuple]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM papers WHERE id=?', (paper_id,))
            return cursor.fetchone()


