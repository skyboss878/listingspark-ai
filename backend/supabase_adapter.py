"""
Supabase-backed replacement for sqlite_auth.py, sqlite_db_adapter.py, and the
Mongo-style shim in server.py. Same method signatures/interfaces so no route
code needs to change.
"""

import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List

from passlib.context import CryptContext
from supabase import create_client, Client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def _get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set in .env")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _serialize(v):
    if hasattr(v, "isoformat"):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _serialize(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_serialize(item) for item in v]
    if hasattr(v, "value"):
        return v.value
    return v


def _clean_row(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: _serialize(v) for k, v in d.items()}


# ==================== AUTH ====================

class SupabaseAuth:
    def __init__(self, db_path: str = None):
        self.client: Optional[Client] = None

    async def init_db(self):
        self.client = _get_client()
        print("✅ Supabase auth initialized")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    async def create_user(self, email: str, password: str, full_name: str,
                           company: Optional[str] = None, phone: Optional[str] = None,
                           role: str = "agent") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if not self.client:
            return None, "Database not initialized"
        existing = self.client.table("users").select("id").eq("email", email).execute()
        if existing.data:
            return None, "Email already registered"
        user_id = str(uuid.uuid4())
        password_hash = self.get_password_hash(password)
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.client.table("users").insert({
                "id": user_id, "email": email, "password_hash": password_hash,
                "full_name": full_name, "company": company, "phone": phone,
                "role": role, "is_active": True, "created_at": now, "updated_at": now,
            }).execute()
            return {
                "id": user_id, "email": email, "full_name": full_name,
                "company": company, "phone": phone, "role": role,
                "is_active": True, "created_at": now
            }, None
        except Exception as e:
            return None, f"Failed to create user: {str(e)}"

    async def authenticate_user(self, email: str, password: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        if not self.client:
            return None, "Database not initialized"
        result = self.client.table("users").select(
            "id, email, password_hash, full_name, company, phone, role, is_active, created_at"
        ).eq("email", email).execute()
        if not result.data:
            return None, "Invalid email or password"
        row = result.data[0]
        if not self.verify_password(password, row["password_hash"]):
            return None, "Invalid email or password"
        if not row["is_active"]:
            return None, "Account is inactive"
        return {
            "id": row["id"], "email": row["email"], "full_name": row["full_name"],
            "company": row["company"], "phone": row["phone"], "role": row["role"],
            "is_active": bool(row["is_active"]), "created_at": row["created_at"]
        }, None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None
        result = self.client.table("users").select(
            "id, email, full_name, company, phone, role, is_active, created_at"
        ).eq("id", user_id).execute()
        if not result.data:
            return None
        row = result.data[0]
        return {
            "id": row["id"], "email": row["email"], "full_name": row["full_name"],
            "company": row["company"], "phone": row["phone"], "role": row["role"],
            "is_active": bool(row["is_active"]), "created_at": row["created_at"]
        }

    def close(self):
        pass


# ==================== LISTINGS / MLS / DASHBOARD ====================

class SupabaseDB:
    def __init__(self):
        self.client = _get_client()

    def create_listing(self, listing: Dict) -> Dict:
        row = _clean_row(listing)
        self.client.table("listings").insert(row).execute()
        return listing

    def get_listings(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        q = self.client.table("listings").select("*").eq("user_id", user_id)
        if status:
            q = q.eq("status", status)
        result = q.order("created_at", desc=True).limit(100).execute()
        return result.data or []

    def get_listing_by_id(self, listing_id: str, user_id: str) -> Optional[Dict]:
        result = self.client.table("listings").select("*").eq("id", listing_id).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    def count_listings(self, user_id: str, status: Optional[str] = None) -> int:
        q = self.client.table("listings").select("id", count="exact").eq("user_id", user_id)
        if status:
            q = q.eq("status", status)
        result = q.execute()
        return result.count or 0

    def get_listings_by_status(self, user_id: str) -> Dict[str, int]:
        result = self.client.table("listings").select("status").eq("user_id", user_id).execute()
        counts: Dict[str, int] = {}
        for row in (result.data or []):
            s = row.get("status")
            counts[s] = counts.get(s, 0) + 1
        return counts

    def create_mls_account(self, account: Dict) -> Dict:
        row = _clean_row(account)
        row["provider"] = str(account["provider"])
        self.client.table("mls_accounts").insert(row).execute()
        return account

    def get_mls_accounts(self, user_id: str) -> List[Dict]:
        result = self.client.table("mls_accounts").select("*").eq("user_id", user_id).execute()
        return result.data or []

    def count_mls_accounts(self, user_id: str) -> int:
        result = self.client.table("mls_accounts").select("id", count="exact").eq("user_id", user_id).execute()
        return result.count or 0

    def get_dashboard_stats(self, user_id: str) -> Dict[str, Any]:
        total_result = self.client.table("listings").select("id", count="exact").eq("user_id", user_id).execute()
        total_listings = total_result.count or 0
        published_result = self.client.table("listings").select("id", count="exact").eq("user_id", user_id).in_(
            "status", ["published", "syndicated"]
        ).execute()
        published = published_result.count or 0
        status_counts = self.get_listings_by_status(user_id)
        mls_result = self.client.table("mls_accounts").select("id", count="exact").eq("user_id", user_id).execute()
        mls_accounts = mls_result.count or 0
        recent_result = self.client.table("listings").select("*").eq("user_id", user_id).order(
            "created_at", desc=True
        ).limit(5).execute()
        recent_listings = recent_result.data or []
        return {
            "total_listings": total_listings, "published": published,
            "status_counts": status_counts, "mls_accounts": mls_accounts,
            "recent_listings": recent_listings
        }


# ==================== MONGO-STYLE SHIM (for get_mongo_db()) ====================

class _SupabaseCollection:
    def __init__(self, client: Client, name: str):
        self.client = client
        self.name = name

    async def insert_one(self, doc: Dict):
        row = {k: v for k, v in doc.items() if k != "_id"}
        row = _clean_row(row)
        self.client.table(self.name).insert(row).execute()

    def _apply_query(self, q, query: Optional[Dict]):
        for k, v in (query or {}).items():
            q = q.eq(k, _serialize(v))
        return q

    async def find_one(self, query: Optional[Dict] = None, *a, **kw):
        try:
            q = self.client.table(self.name).select("*")
            q = self._apply_query(q, query)
            result = q.limit(1).execute()
            return result.data[0] if result.data else None
        except Exception:
            return None

    def find(self, query: Optional[Dict] = None, *a, **kw):
        return _SupabaseCursor(self, query)

    async def update_one(self, query: Dict, update: Dict, *a, **kw):
        sets = update.get("$set", {}) if isinstance(update, dict) else {}
        if not sets:
            return
        row = _clean_row(sets)
        q = self.client.table(self.name).update(row)
        q = self._apply_query(q, query)
        q.execute()

    async def delete_one(self, query: Dict, *a, **kw):
        q = self.client.table(self.name).delete()
        q = self._apply_query(q, query)
        q.execute()

    async def delete_many(self, query: Dict, *a, **kw):
        await self.delete_one(query)

    async def count_documents(self, query: Optional[Dict] = None, *a, **kw):
        try:
            q = self.client.table(self.name).select("id", count="exact")
            q = self._apply_query(q, query)
            result = q.execute()
            return result.count or 0
        except Exception:
            return 0


class _SupabaseCursor:
    def __init__(self, coll: _SupabaseCollection, query: Optional[Dict]):
        self.coll = coll
        self.query = query
        self._limit_n = 1000
        self._sort_field = None
        self._sort_desc = True

    def sort(self, field, direction=-1):
        self._sort_field = field
        self._sort_desc = direction == -1
        return self

    def limit(self, n):
        self._limit_n = n
        return self

    def skip(self, n):
        return self

    def _fetch(self):
        try:
            q = self.coll.client.table(self.coll.name).select("*")
            q = self.coll._apply_query(q, self.query)
            if self._sort_field:
                q = q.order(self._sort_field, desc=self._sort_desc)
            q = q.limit(self._limit_n)
            result = q.execute()
            return result.data or []
        except Exception:
            return []

    async def to_list(self, length=None):
        rows = self._fetch()
        return rows[:length] if length else rows

    def __aiter__(self):
        self._rows = iter(self._fetch())
        return self

    async def __anext__(self):
        try:
            return next(self._rows)
        except StopIteration:
            raise StopAsyncIteration


class _SupabaseMongoDB:
    def __init__(self):
        self.client = _get_client()

    def __getattr__(self, name):
        return _SupabaseCollection(self.client, name)

    def __getitem__(self, name):
        return _SupabaseCollection(self.client, name)


_supabase_mongo_db = None

async def get_supabase_mongo_db():
    global _supabase_mongo_db
    if _supabase_mongo_db is None:
        _supabase_mongo_db = _SupabaseMongoDB()
    return _supabase_mongo_db
