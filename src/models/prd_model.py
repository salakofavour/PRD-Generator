import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class PRDDatabase:
    def __init__(self, db_path: str = "data/prd_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # PRDs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prds (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_input TEXT,
                status TEXT DEFAULT 'draft',
                feedback TEXT,
                is_approved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Version history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prd_versions (
                id TEXT PRIMARY KEY,
                prd_id TEXT,
                version INTEGER,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changes_summary TEXT,
                FOREIGN KEY (prd_id) REFERENCES prds (id)
            )
        ''')
        
        # Chat sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                prd_id TEXT,
                messages TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prd_id) REFERENCES prds (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_prd(self, title: str, content: str, user_input: str, prd_id: str = None) -> str:
        """Save a new PRD or update existing one"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if prd_id is None:
            # Create new PRD
            prd_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO prds (id, title, content, user_input)
                VALUES (?, ?, ?, ?)
            ''', (prd_id, title, content, user_input))
            version = 1
        else:
            # Update existing PRD
            cursor.execute('''
                UPDATE prds 
                SET content = ?, updated_at = CURRENT_TIMESTAMP, version = version + 1
                WHERE id = ?
            ''', (content, prd_id))
            
            # Get current version
            cursor.execute('SELECT version FROM prds WHERE id = ?', (prd_id,))
            version = cursor.fetchone()[0]
        
        # Save version history
        version_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO prd_versions (id, prd_id, version, content)
            VALUES (?, ?, ?, ?)
        ''', (version_id, prd_id, version, content))
        
        conn.commit()
        conn.close()
        return prd_id
    
    def get_prd(self, prd_id: str) -> Optional[Dict]:
        """Get PRD by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prds WHERE id = ?', (prd_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            prd = dict(zip(columns, row))
            conn.close()
            return prd
        
        conn.close()
        return None
    
    def get_all_prds(self) -> List[Dict]:
        """Get all PRDs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prds ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        prds = [dict(zip(columns, row)) for row in rows]
        conn.close()
        return prds
    
    def get_prd_versions(self, prd_id: str) -> List[Dict]:
        """Get all versions of a PRD"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prd_versions 
            WHERE prd_id = ? 
            ORDER BY version DESC
        ''', (prd_id,))
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        versions = [dict(zip(columns, row)) for row in rows]
        conn.close()
        return versions
    
    def approve_prd(self, prd_id: str, feedback: str = ""):
        """Mark PRD as approved for training data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE prds 
            SET is_approved = TRUE, feedback = ?, status = 'approved'
            WHERE id = ?
        ''', (feedback, prd_id))
        
        conn.commit()
        conn.close()
    
    def get_approved_prds(self) -> List[Dict]:
        """Get all approved PRDs for training"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM prds WHERE is_approved = TRUE')
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        prds = [dict(zip(columns, row)) for row in rows]
        conn.close()
        return prds
    
    def save_chat_session(self, prd_id: str, messages: List[Dict]) -> str:
        """Save chat session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        session_id = str(uuid.uuid4())
        messages_json = json.dumps(messages)
        
        cursor.execute('''
            INSERT INTO chat_sessions (id, prd_id, messages)
            VALUES (?, ?, ?)
        ''', (session_id, prd_id, messages_json))
        
        conn.commit()
        conn.close()
        return session_id