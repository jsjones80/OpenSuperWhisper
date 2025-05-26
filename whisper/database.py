"""
Database module for OpenSuperWhisper Windows
Handles storage and retrieval of recordings and transcriptions
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import uuid


def get_user_data_directory() -> Path:
    """Get the user data directory for OpenSuperWhisper"""
    if os.name == 'nt':
        # Windows: Use AppData/Roaming
        data_dir = Path(os.environ.get('APPDATA', '')) / 'OpenSuperWhisper'
    else:
        # Other systems: Use home directory
        data_dir = Path.home() / '.opensuperwhisper'

    data_dir.mkdir(exist_ok=True)
    return data_dir


def get_recordings_directory() -> Path:
    """Get the recordings directory"""
    recordings_dir = get_user_data_directory() / 'recordings'
    recordings_dir.mkdir(exist_ok=True)
    return recordings_dir


def get_database_path() -> Path:
    """Get the database file path"""
    return get_user_data_directory() / 'recordings.db'


class Recording:
    """Recording data model"""

    def __init__(
        self,
        id: str = None,
        timestamp: datetime = None,
        filename: str = "",
        transcription: str = "",
        duration: float = 0.0,
        language: str = "",
        model_used: str = "",
        file_size: int = 0,
        settings: Dict[str, Any] = None
    ):
        self.id = id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.now()
        self.filename = filename
        self.transcription = transcription
        self.duration = duration
        self.language = language
        self.model_used = model_used
        self.file_size = file_size
        self.settings = settings or {}

    @property
    def file_path(self) -> Path:
        """Get the full path to the recording file"""
        return get_recordings_directory() / self.filename

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'filename': self.filename,
            'transcription': self.transcription,
            'duration': self.duration,
            'language': self.language,
            'model_used': self.model_used,
            'file_size': self.file_size,
            'settings': json.dumps(self.settings)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recording':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            filename=data['filename'],
            transcription=data['transcription'],
            duration=data['duration'],
            language=data['language'],
            model_used=data['model_used'],
            file_size=data['file_size'],
            settings=json.loads(data['settings']) if data['settings'] else {}
        )


class RecordingDatabase:
    """SQLite database for storing recordings"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = get_database_path()
        else:
            self.db_path = Path(db_path)
        self._init_database()

    def _init_database(self):
        """Initialize the database and create tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recordings (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    transcription TEXT NOT NULL,
                    duration REAL NOT NULL,
                    language TEXT,
                    model_used TEXT,
                    file_size INTEGER,
                    settings TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes for better search performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON recordings(timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_transcription
                ON recordings(transcription)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_language
                ON recordings(language)
            """)

            conn.commit()

    def add_recording(self, recording: Recording) -> bool:
        """Add a new recording to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = recording.to_dict()
                conn.execute("""
                    INSERT INTO recordings
                    (id, timestamp, filename, transcription, duration,
                     language, model_used, file_size, settings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['id'], data['timestamp'], data['filename'],
                    data['transcription'], data['duration'], data['language'],
                    data['model_used'], data['file_size'], data['settings']
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Failed to add recording: {e}")
            return False

    def get_recording(self, recording_id: str) -> Optional[Recording]:
        """Get a recording by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM recordings WHERE id = ?",
                    (recording_id,)
                )
                row = cursor.fetchone()
                if row:
                    return Recording.from_dict(dict(row))
                return None
        except Exception as e:
            print(f"Failed to get recording: {e}")
            return None

    def get_all_recordings(self, limit: int = None, offset: int = 0) -> List[Recording]:
        """Get all recordings, optionally with pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                query = "SELECT * FROM recordings ORDER BY timestamp DESC"
                params = []

                if limit:
                    query += " LIMIT ? OFFSET ?"
                    params.extend([limit, offset])

                cursor = conn.execute(query, params)
                rows = cursor.fetchall()

                return [Recording.from_dict(dict(row)) for row in rows]
        except Exception as e:
            print(f"Failed to get recordings: {e}")
            return []

    def search_recordings(
        self,
        query: str,
        language: str = None,
        date_from: datetime = None,
        date_to: datetime = None,
        limit: int = None
    ) -> List[Recording]:
        """Search recordings by text, language, and date range"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                sql_query = """
                    SELECT * FROM recordings
                    WHERE transcription LIKE ?
                """
                params = [f"%{query}%"]

                if language:
                    sql_query += " AND language = ?"
                    params.append(language)

                if date_from:
                    sql_query += " AND timestamp >= ?"
                    params.append(date_from.isoformat())

                if date_to:
                    sql_query += " AND timestamp <= ?"
                    params.append(date_to.isoformat())

                sql_query += " ORDER BY timestamp DESC"

                if limit:
                    sql_query += " LIMIT ?"
                    params.append(limit)

                cursor = conn.execute(sql_query, params)
                rows = cursor.fetchall()

                return [Recording.from_dict(dict(row)) for row in rows]
        except Exception as e:
            print(f"Failed to search recordings: {e}")
            return []

    def update_recording(self, recording: Recording) -> bool:
        """Update an existing recording"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data = recording.to_dict()
                conn.execute("""
                    UPDATE recordings SET
                        timestamp = ?, filename = ?, transcription = ?,
                        duration = ?, language = ?, model_used = ?,
                        file_size = ?, settings = ?
                    WHERE id = ?
                """, (
                    data['timestamp'], data['filename'], data['transcription'],
                    data['duration'], data['language'], data['model_used'],
                    data['file_size'], data['settings'], data['id']
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Failed to update recording: {e}")
            return False

    def delete_recording(self, recording_id: str) -> bool:
        """Delete a recording from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM recordings WHERE id = ?",
                    (recording_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Failed to delete recording: {e}")
            return False

    def delete_all_recordings(self) -> bool:
        """Delete all recordings from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM recordings")
                conn.commit()
                return True
        except Exception as e:
            print(f"Failed to delete all recordings: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_recordings,
                        SUM(duration) as total_duration,
                        SUM(file_size) as total_file_size,
                        AVG(duration) as avg_duration,
                        MIN(timestamp) as oldest_recording,
                        MAX(timestamp) as newest_recording
                    FROM recordings
                """)
                row = cursor.fetchone()

                # Get language distribution
                cursor = conn.execute("""
                    SELECT language, COUNT(*) as count
                    FROM recordings
                    WHERE language IS NOT NULL AND language != ''
                    GROUP BY language
                    ORDER BY count DESC
                """)
                languages = dict(cursor.fetchall())

                # Get model usage
                cursor = conn.execute("""
                    SELECT model_used, COUNT(*) as count
                    FROM recordings
                    WHERE model_used IS NOT NULL AND model_used != ''
                    GROUP BY model_used
                    ORDER BY count DESC
                """)
                models = dict(cursor.fetchall())

                return {
                    'total_recordings': row[0] or 0,
                    'total_duration': row[1] or 0.0,
                    'total_file_size': row[2] or 0,
                    'avg_duration': row[3] or 0.0,
                    'oldest_recording': row[4],
                    'newest_recording': row[5],
                    'languages': languages,
                    'models': models
                }
        except Exception as e:
            print(f"Failed to get statistics: {e}")
            return {}

    def cleanup_old_recordings(self, days: int = 30) -> int:
        """Delete recordings older than specified days"""
        try:
            cutoff_date = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=days)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM recordings WHERE timestamp < ?",
                    (cutoff_date.isoformat(),)
                )
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Failed to cleanup old recordings: {e}")
            return 0


# Singleton instance
_database = None

def get_database() -> RecordingDatabase:
    """Get singleton database instance"""
    global _database
    if _database is None:
        _database = RecordingDatabase()
    return _database
