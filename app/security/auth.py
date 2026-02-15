"""
Authentication module — JWT-based user management for hospital deployment.

Provides:
- SQLite-backed user registry with bcrypt password hashing
- JWT token creation / verification
- Default admin user seeded on first startup
"""

import sqlite3
import os
import json
import logging
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# Role / Department constants
# ---------------------------------------------------------------------------
ROLE_HIERARCHY = {
    "admin": 100,
    "doctor": 80,
    "nurse": 60,
    "technician": 50,
    "researcher": 40,
    "viewer": 10,
}

# Default department access per role (admin gets everything)
DEFAULT_ROLE_DEPARTMENTS: Dict[str, List[str]] = {
    "admin": [],       # empty → means ALL departments
    "doctor": [],      # doctors default to all departments too
    "nurse": ["nursing", "general", "emergency"],
    "technician": ["laboratory", "radiology"],
    "researcher": ["general"],
    "viewer": ["general"],
}


# ---------------------------------------------------------------------------
# SQLite User DB
# ---------------------------------------------------------------------------
class UserDB:
    """Lightweight SQLite user store for small hospital deployments."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.USERS_DB_PATH
        self._init_db()
        self._seed_admin()

    @contextmanager
    def _conn(self):
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    username    TEXT UNIQUE NOT NULL,
                    full_name   TEXT NOT NULL DEFAULT '',
                    hashed_pw   TEXT NOT NULL,
                    role        TEXT NOT NULL DEFAULT 'viewer',
                    departments TEXT NOT NULL DEFAULT '["general"]',
                    is_active   INTEGER NOT NULL DEFAULT 1,
                    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)

    def _seed_admin(self):
        """Create the default admin user if no users exist."""
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
            if row["cnt"] == 0:
                all_depts = json.dumps(settings.departments_list)
                conn.execute(
                    "INSERT INTO users (username, full_name, hashed_pw, role, departments) VALUES (?, ?, ?, ?, ?)",
                    ("admin", "System Administrator", hash_password("admin123"), "admin", all_depts),
                )
                logger.info("Seeded default admin user (admin / admin123)")

    # ----- CRUD ----------------------------------------------------------

    def create_user(
        self,
        username: str,
        password: str,
        role: str = "viewer",
        departments: Optional[List[str]] = None,
        full_name: str = "",
    ) -> dict:
        if role not in ROLE_HIERARCHY:
            raise ValueError(f"Invalid role '{role}'. Must be one of {list(ROLE_HIERARCHY.keys())}")

        valid_depts = settings.departments_list
        dept_list = departments or DEFAULT_ROLE_DEPARTMENTS.get(role, ["general"])
        # admin/doctor with empty default → give all departments
        if not dept_list:
            dept_list = valid_depts
        for d in dept_list:
            if d not in valid_depts:
                raise ValueError(f"Invalid department '{d}'. Valid: {valid_depts}")

        with self._conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (username, full_name, hashed_pw, role, departments) VALUES (?, ?, ?, ?, ?)",
                    (username, full_name, hash_password(password), role, json.dumps(dept_list)),
                )
            except sqlite3.IntegrityError:
                raise ValueError(f"Username '{username}' already exists")
        return self.get_user(username)

    def get_user(self, username: str) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "full_name": row["full_name"],
                "hashed_pw": row["hashed_pw"],
                "role": row["role"],
                "departments": json.loads(row["departments"]),
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"],
            }

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        user = self.get_user(username)
        if not user or not user["is_active"]:
            return None
        if not verify_password(password, user["hashed_pw"]):
            return None
        return user

    def list_users(self) -> List[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT id, username, full_name, role, departments, is_active, created_at FROM users").fetchall()
            return [
                {
                    "id": r["id"],
                    "username": r["username"],
                    "full_name": r["full_name"],
                    "role": r["role"],
                    "departments": json.loads(r["departments"]),
                    "is_active": bool(r["is_active"]),
                    "created_at": r["created_at"],
                }
                for r in rows
            ]

    def delete_user(self, username: str) -> bool:
        with self._conn() as conn:
            cur = conn.execute("DELETE FROM users WHERE username = ? AND role != 'admin'", (username,))
            return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
user_db = UserDB()
