"""
SQLite Authentication Module for ListingSpark AI
Handles user authentication and management with SQLite database
"""

import sqlite3
import uuid
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from passlib.context import CryptContext
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SQLiteAuth:
    def __init__(self, db_path: str = None):
        db_path = db_path or os.getenv("SQLITE_DB", "listingspark.db")
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
    
    async def init_db(self):
        """Initialize the SQLite database and create tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                company TEXT,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'agent',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        self.conn.commit()
        print("✅ SQLite database initialized")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        company: Optional[str] = None,
        phone: Optional[str] = None,
        role: str = "agent"
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Create a new user"""
        
        if not self.conn:
            return None, "Database not initialized"
        
        # Check if user already exists
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return None, "Email already registered"
        
        # Create user
        user_id = str(uuid.uuid4())
        password_hash = self.get_password_hash(password)
        now = datetime.utcnow().isoformat()
        
        try:
            cursor.execute("""
                INSERT INTO users (id, email, password_hash, full_name, company, phone, role, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, (user_id, email, password_hash, full_name, company, phone, role, now, now))
            
            self.conn.commit()
            
            user_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "company": company,
                "phone": phone,
                "role": role,
                "is_active": True,
                "created_at": now
            }
            
            return user_data, None
            
        except Exception as e:
            return None, f"Failed to create user: {str(e)}"
    
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Authenticate a user with email and password"""
        
        if not self.conn:
            return None, "Database not initialized"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, email, password_hash, full_name, company, phone, role, is_active, created_at
            FROM users
            WHERE email = ?
        """, (email,))
        
        row = cursor.fetchone()
        
        if not row:
            return None, "Invalid email or password"
        
        if not self.verify_password(password, row["password_hash"]):
            return None, "Invalid email or password"
        
        if not row["is_active"]:
            return None, "Account is inactive"
        
        user_data = {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "company": row["company"],
            "phone": row["phone"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"]
        }
        
        return user_data, None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        
        if not self.conn:
            return None
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, email, full_name, company, phone, role, is_active, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"],
            "company": row["company"],
            "phone": row["phone"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"]
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
