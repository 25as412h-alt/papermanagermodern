import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

class Database:
    def __init__(self, db_path: str = 'papers.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Papers table
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
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # Add any indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_papers_title ON papers(title)')
            
            conn.commit()
    
    def _get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def add_paper(self, paper_data: Dict[str, Any]) -> int:
        """Add a new paper to the database
        
        Args:
            paper_data: Dictionary containing paper information
                Required keys: title
                Optional keys: title_en, authors, authors_en, year, tags, summary, fulltext, original_file
                
        Returns:
            int: ID of the newly created paper
        """
        current_time = datetime.now().isoformat()
        paper_data['created_at'] = current_time
        paper_data['updated_at'] = current_time
        
        # Convert tags list to JSON string if it's a list
        if 'tags' in paper_data and isinstance(paper_data['tags'], list):
            paper_data['tags'] = json.dumps(paper_data['tags'], ensure_ascii=False)
            
        columns = ', '.join(paper_data.keys())
        placeholders = ', '.join(['?'] * len(paper_data))
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'INSERT INTO papers ({columns}) VALUES ({placeholders})',
                list(paper_data.values())
            )
            paper_id = cursor.lastrowid
            conn.commit()
            
        return paper_id
    
    def get_paper(self, paper_id: int) -> Optional[Dict[str, Any]]:
        """Get a paper by ID
        
        Args:
            paper_id: ID of the paper to retrieve
            
        Returns:
            Dictionary containing paper data or None if not found
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM papers WHERE id = ?', (paper_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            # Convert row to dictionary
            columns = [description[0] for description in cursor.description]
            paper = dict(zip(columns, row))
            
            # Convert JSON strings back to Python objects
            if paper.get('tags'):
                paper['tags'] = json.loads(paper['tags'])
                
            return paper
    
    def update_paper(self, paper_id: int, update_data: Dict[str, Any]) -> bool:
        """Update an existing paper
        
        Args:
            paper_id: ID of the paper to update
            update_data: Dictionary containing fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        if not update_data:
            return False
            
        # Don't update created_at, but update updated_at
        if 'created_at' in update_data:
            del update_data['created_at']
            
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Convert tags list to JSON string if it's a list
        if 'tags' in update_data and isinstance(update_data['tags'], list):
            update_data['tags'] = json.dumps(update_data['tags'], ensure_ascii=False)
            
        set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
        values = list(update_data.values())
        values.append(paper_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'UPDATE papers SET {set_clause} WHERE id = ?',
                values
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_paper(self, paper_id: int) -> bool:
        """Delete a paper from the database
        
        Args:
            paper_id: ID of the paper to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM papers WHERE id = ?', (paper_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def search_papers(self, query: str = None, **filters) -> List[Dict[str, Any]]:
        """Search for papers with optional full-text search and filtering
        
        Args:
            query: Full-text search query string
            **filters: Additional filters (e.g., year=2023, tags=['ml', 'ai'])
            
        Returns:
            List of matching papers
        """
        conditions = []
        params = []
        
        # Handle full-text search
        if query:
            # Simple LIKE search for now - can be enhanced with FTS5 later
            conditions.append("(title LIKE ? OR authors LIKE ? OR summary LIKE ?)")
            search_term = f"%{query}%"
            params.extend([search_term, search_term, search_term])
        
        # Handle filters
        for field, value in filters.items():
            if field == 'tags' and value:
                if isinstance(value, str):
                    value = [value]
                if isinstance(value, list):
                    # Search for any of the tags
                    tag_conditions = []
                    for tag in value:
                        tag_conditions.append("tags LIKE ?")
                        params.append(f'%"{tag}"%')
                    conditions.append(f"({' OR '.join(tag_conditions)})")
            elif field in ['title', 'authors', 'year'] and value is not None:
                if field == 'year' and isinstance(value, (list, tuple)) and len(value) == 2:
                    # Handle year range
                    conditions.append("year BETWEEN ? AND ?")
                    params.extend(value)
                else:
                    conditions.append(f"{field} = ?")
                    params.append(value)
        
        # Build the query
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM papers WHERE {where_clause} ORDER BY updated_at DESC"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            papers = []
            for row in cursor.fetchall():
                # Convert row to dictionary
                columns = [description[0] for description in cursor.description]
                paper = dict(zip(columns, row))
                
                # Convert JSON strings back to Python objects
                if paper.get('tags'):
                    paper['tags'] = json.loads(paper['tags'])
                    
                papers.append(paper)
                
            return papers
    
    def export_to_csv(self, file_path: str, papers: List[Dict[str, Any]] = None) -> bool:
        """Export papers to a CSV file
        
        Args:
            file_path: Path to save the CSV file
            papers: List of papers to export. If None, exports all papers.
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        import csv
        
        if papers is None:
            papers = self.search_papers()
        
        if not papers:
            return False
            
        # Flatten the data for CSV
        fieldnames = [
            'id', 'title', 'title_en', 'authors', 'authors_en', 'year',
            'tags', 'summary', 'created_at', 'updated_at'
        ]
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for paper in papers:
                    # Create a copy to avoid modifying the original
                    row = paper.copy()
                    
                    # Convert tags list to string
                    if 'tags' in row and isinstance(row['tags'], list):
                        row['tags'] = ', '.join(row['tags'])
                        
                    # Only include the fields we want in the CSV
                    row = {k: v for k, v in row.items() if k in fieldnames}
                    writer.writerow(row)
                    
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database
        
        Args:
            backup_path: Path to save the backup file
            
        Returns:
            bool: True if backup was successful, False otherwise
        """
        import shutil
        
        try:
            shutil.copy2(self.db_path, backup_path)
            return True
        except Exception as e:
            print(f"Error creating database backup: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore the database from a backup
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            bool: True if restore was successful, False otherwise
        """
        import shutil
        
        try:
            shutil.copy2(backup_path, self.db_path)
            return True
        except Exception as e:
            print(f"Error restoring database: {e}")
            return False