import os
import sqlite3
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

class SQLiteDB:
    def __init__(self, db_path=None):
        db_path = db_path or os.getenv('SQLITE_DB', 'listingspark.db')
        self.db_path = db_path
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def dict_factory(self, row):
        """Convert row to dict"""
        return {key: row[key] for key in row.keys()}
    
    # Listings operations
    def get_listings(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT * FROM listings WHERE user_id = ? AND status = ? ORDER BY created_at DESC LIMIT 100",
                (user_id, status)
            )
        else:
            cursor.execute(
                "SELECT * FROM listings WHERE user_id = ? ORDER BY created_at DESC LIMIT 100",
                (user_id,)
            )
        
        rows = cursor.fetchall()
        conn.close()
        return [self.dict_factory(row) for row in rows]
    
    def get_listing_by_id(self, listing_id: str, user_id: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM listings WHERE id = ? AND user_id = ?",
            (listing_id, user_id)
        )
        
        row = cursor.fetchone()
        conn.close()
        return self.dict_factory(row) if row else None
    
    def count_listings(self, user_id: str, status: Optional[str] = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if status:
            cursor.execute(
                "SELECT COUNT(*) FROM listings WHERE user_id = ? AND status = ?",
                (user_id, status)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM listings WHERE user_id = ?",
                (user_id,)
            )
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_listings_by_status(self, user_id: str) -> Dict[str, int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT status, COUNT(*) as count FROM listings WHERE user_id = ? GROUP BY status",
            (user_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        return {row['status']: row['count'] for row in rows}
    
    # MLS accounts operations
    def ensure_mls_schema(self):
        """Rebuild mls_accounts with model-matching schema (old table was never used)"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(mls_accounts)")
        cols = [r[1] for r in cur.fetchall()]
        if 'provider' not in cols:
            cur.execute("DROP TABLE IF EXISTS mls_accounts")
            cur.execute('''CREATE TABLE mls_accounts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                provider TEXT NOT NULL,
                account_name TEXT NOT NULL,
                client_id TEXT,
                client_secret TEXT,
                api_endpoint TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                is_connected INTEGER DEFAULT 0,
                last_sync TEXT,
                created_at TEXT
            )''')
            conn.commit()
        conn.close()

    def create_mls_account(self, account: Dict) -> Dict:
        self.ensure_mls_schema()
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            '''INSERT INTO mls_accounts
               (id, user_id, provider, account_name, client_id, client_secret,
                api_endpoint, description, is_active, is_connected, last_sync, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (account['id'], account['user_id'], str(account['provider']),
             account['account_name'], account.get('client_id'), account.get('client_secret'),
             account.get('api_endpoint'), account.get('description'),
             1 if account.get('is_active', True) else 0,
             1 if account.get('is_connected') else 0,
             account.get('last_sync'),
             str(account.get('created_at', '')))
        )
        conn.commit()
        conn.close()
        return account

    def get_mls_accounts(self, user_id: str) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM mls_accounts WHERE user_id = ?",
            (user_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        return [self.dict_factory(row) for row in rows]
    
    def count_mls_accounts(self, user_id: str) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM mls_accounts WHERE user_id = ?",
            (user_id,)
        )
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        """Get dashboard statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get total listings
        cursor.execute("SELECT COUNT(*) FROM listings WHERE user_id = ?", (user_id,))
        total_listings = cursor.fetchone()[0]
        
        # Get published count
        cursor.execute(
            "SELECT COUNT(*) FROM listings WHERE user_id = ? AND status IN ('published', 'syndicated')",
            (user_id,)
        )
        published = cursor.fetchone()[0]
        
        # Get status counts
        cursor.execute(
            "SELECT status, COUNT(*) as count FROM listings WHERE user_id = ? GROUP BY status",
            (user_id,)
        )
        status_rows = cursor.fetchall()
        status_counts = {row['status']: row['count'] for row in status_rows}
        
        # Get MLS accounts count
        cursor.execute("SELECT COUNT(*) FROM mls_accounts WHERE user_id = ?", (user_id,))
        mls_accounts = cursor.fetchone()[0]
        
        # Get recent listings
        cursor.execute(
            "SELECT * FROM listings WHERE user_id = ? ORDER BY created_at DESC LIMIT 5",
            (user_id,)
        )
        recent_rows = cursor.fetchall()
        recent_listings = [self.dict_factory(row) for row in recent_rows]
        
        conn.close()
        
        return {
            "total_listings": total_listings,
            "published": published,
            "status_counts": status_counts,
            "mls_accounts": mls_accounts,
            "recent_listings": recent_listings
        }

# Global instance
sqlite_db = SQLiteDB()
