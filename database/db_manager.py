import sqlite3
import json
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any


class DatabaseManager:
    """Manages SQLite database operations for vacancies."""

    # Thread-local storage for database connections
    _local = threading.local()

    def __init__(self, db_path: str = "vacancies.db"):
        """Initialize database connection."""
        self.db_path = db_path

    def _get_connection(self):
        """Get or create a thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.cursor = self._local.connection.cursor()
            self._create_tables()
        return self._local.connection, self._local.cursor

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            connection, cursor = self._get_connection()
            # Create vacancies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vacancies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    salary_min INTEGER,
                    salary_max INTEGER,
                    currency TEXT,
                    location TEXT,
                    experience TEXT,
                    key_skills TEXT,
                    company TEXT,
                    link TEXT UNIQUE NOT NULL,
                    remote BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create search_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    location TEXT,
                    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    vacancies_found INTEGER DEFAULT 0
                )
            ''')

            connection.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            raise

    def _connect(self):
        """Establish database connection."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            self._create_tables()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def save_vacancy(self, vacancy_data: Dict[str, Any]) -> bool:
        """Save a single vacancy to the database."""
        try:
            connection, cursor = self._get_connection()

            # Convert key_skills to JSON string if it's a list/dict
            key_skills = vacancy_data.get('key_skills', '')
            if isinstance(key_skills, (list, dict)):
                key_skills = json.dumps(key_skills, ensure_ascii=False)

            cursor.execute('''
                INSERT OR REPLACE INTO vacancies
                (title, salary_min, salary_max, currency, location, experience,
                 key_skills, company, link, remote)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vacancy_data.get('title', ''),
                vacancy_data.get('salary_min'),
                vacancy_data.get('salary_max'),
                vacancy_data.get('currency', ''),
                vacancy_data.get('location', ''),
                vacancy_data.get('experience', ''),
                key_skills,
                vacancy_data.get('company', ''),
                vacancy_data.get('link', ''),
                vacancy_data.get('remote', False)
            ))

            connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error saving vacancy: {e}")
            return False

    def save_vacancies_batch(self, vacancies: List[Dict[str, Any]]) -> int:
        """Save multiple vacancies to the database."""
        saved_count = 0
        for vacancy in vacancies:
            if self.save_vacancy(vacancy):
                saved_count += 1
        return saved_count

    def get_all_vacancies(self) -> List[Dict[str, Any]]:
        """Retrieve all vacancies from the database."""
        try:
            connection, cursor = self._get_connection()
            cursor.execute('''
                SELECT id, title, salary_min, salary_max, currency, location,
                       experience, key_skills, company, link, remote, created_at
                FROM vacancies
                ORDER BY created_at DESC
            ''')

            rows = cursor.fetchall()
            vacancies = []
            for row in rows:
                vacancy = {
                    'id': row[0],
                    'title': row[1],
                    'salary_min': row[2],
                    'salary_max': row[3],
                    'currency': row[4],
                    'location': row[5],
                    'experience': row[6],
                    'key_skills': row[7],
                    'company': row[8],
                    'link': row[9],
                    'remote': bool(row[10]),
                    'created_at': row[11]
                }
                vacancies.append(vacancy)

            return vacancies
        except sqlite3.Error as e:
            print(f"Error retrieving vacancies: {e}")
            return []

    def search_vacancies(self, keyword: str = None, location: str = None,
                        company: str = None, remote: bool = None) -> List[Dict[str, Any]]:
        """Search vacancies with filters."""
        try:
            connection, cursor = self._get_connection()
            query = '''
                SELECT id, title, salary_min, salary_max, currency, location,
                       experience, key_skills, company, link, remote, created_at
                FROM vacancies
                WHERE 1=1
            '''
            params = []

            if keyword:
                query += " AND (title LIKE ? OR key_skills LIKE ? OR company LIKE ?)"
                keyword_pattern = f"%{keyword}%"
                params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

            if location:
                query += " AND location LIKE ?"
                params.append(f"%{location}%")

            if company:
                query += " AND company LIKE ?"
                params.append(f"%{company}%")

            if remote is not None:
                query += " AND remote = ?"
                params.append(remote)

            query += " ORDER BY created_at DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            vacancies = []
            for row in rows:
                vacancy = {
                    'id': row[0],
                    'title': row[1],
                    'salary_min': row[2],
                    'salary_max': row[3],
                    'currency': row[4],
                    'location': row[5],
                    'experience': row[6],
                    'key_skills': row[7],
                    'company': row[8],
                    'link': row[9],
                    'remote': bool(row[10]),
                    'created_at': row[11]
                }
                vacancies.append(vacancy)

            return vacancies
        except sqlite3.Error as e:
            print(f"Error searching vacancies: {e}")
            return []

    def save_search_history(self, keyword: str, location: str = None, vacancies_found: int = 0):
        """Save search history."""
        try:
            connection, cursor = self._get_connection()
            cursor.execute('''
                INSERT INTO search_history (keyword, location, vacancies_found)
                VALUES (?, ?, ?)
            ''', (keyword, location, vacancies_found))

            connection.commit()
        except sqlite3.Error as e:
            print(f"Error saving search history: {e}")

    def get_search_history(self) -> List[Dict[str, Any]]:
        """Retrieve search history."""
        try:
            connection, cursor = self._get_connection()
            cursor.execute('''
                SELECT id, keyword, location, search_date, vacancies_found
                FROM search_history
                ORDER BY search_date DESC
                LIMIT 50
            ''')

            rows = cursor.fetchall()
            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'keyword': row[1],
                    'location': row[2],
                    'search_date': row[3],
                    'vacancies_found': row[4]
                })

            return history
        except sqlite3.Error as e:
            print(f"Error retrieving search history: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            connection, cursor = self._get_connection()
            stats = {}

            # Total vacancies
            cursor.execute("SELECT COUNT(*) FROM vacancies")
            stats['total_vacancies'] = cursor.fetchone()[0]

            # Vacancies with salary info
            cursor.execute("SELECT COUNT(*) FROM vacancies WHERE salary_min IS NOT NULL")
            stats['vacancies_with_salary'] = cursor.fetchone()[0]

            # Remote work vacancies
            cursor.execute("SELECT COUNT(*) FROM vacancies WHERE remote = 1")
            stats['remote_vacancies'] = cursor.fetchone()[0]

            # Unique companies
            cursor.execute("SELECT COUNT(DISTINCT company) FROM vacancies WHERE company != ''")
            stats['unique_companies'] = cursor.fetchone()[0]

            # Unique locations
            cursor.execute("SELECT COUNT(DISTINCT location) FROM vacancies WHERE location != ''")
            stats['unique_locations'] = cursor.fetchone()[0]

            return stats
        except sqlite3.Error as e:
            print(f"Error getting statistics: {e}")
            return {}

    def clear_all_data(self) -> bool:
        """Clear all data from database."""
        try:
            connection, cursor = self._get_connection()

            # Clear all tables
            cursor.execute("DELETE FROM vacancies")
            cursor.execute("DELETE FROM search_history")

            connection.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error clearing database: {e}")
            return False

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
