"""
SAMVAD Authentication & User Session Store

Provides SQLite-backed persistence for user accounts, credentials,
OAuth profiles (Google), and active user sessions.
Uses standard library hashlib + secrets + hmac for cryptographically
secure password hashing (PBKDF2-HMAC-SHA256) and signed session tokens.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Generator, Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings


class UserRecord(BaseModel):
    id: str
    email: str
    name: str
    provider: str = "email"  # "email" or "google"
    google_id: Optional[str] = None
    avatar_url: Optional[str] = None
    plan: str = "free"  # "free" or "pro"
    created_at: str
    updated_at: str


class AuthStore:
    """Manages SQLite storage for users and user session tokens."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            settings = get_settings()
            db_path = Path(settings.sqlite_db_path)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    password_hash TEXT,
                    salt TEXT,
                    provider TEXT NOT NULL DEFAULT 'email',
                    google_id TEXT,
                    avatar_url TEXT,
                    plan TEXT NOT NULL DEFAULT 'free',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);

                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

                CREATE TABLE IF NOT EXISTS pro_waitlist (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    user_id TEXT,
                    created_at TEXT NOT NULL,
                    notified INTEGER DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_waitlist_email ON pro_waitlist(email);
                """
            )

            # Seed default demo/admin user "Krrish" if empty so the app has instant out-of-the-box identity
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                now = datetime.now(timezone.utc).isoformat()
                salt = secrets.token_hex(16)
                default_hash = self.hash_password("Samvad@2026", salt)
                conn.execute(
                    """
                    INSERT INTO users (id, email, name, password_hash, salt, provider, avatar_url, plan, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "usr_krrish_default",
                        "krrish@samvad.ai",
                        "Krrish",
                        default_hash,
                        salt,
                        "email",
                        None,
                        "free",
                        now,
                        now,
                    ),
                )
                conn.commit()

    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Derive strong password hash using PBKDF2-HMAC-SHA256 with 100,000 rounds."""
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,
        )
        return dk.hex()

    def create_user_with_password(
        self,
        *,
        email: str,
        password: str,
        name: str,
        plan: str = "free",
    ) -> UserRecord:
        normalized_email = email.strip().lower()
        salt = secrets.token_hex(16)
        pw_hash = self.hash_password(password, salt)
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (id, email, name, password_hash, salt, provider, plan, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'email', ?, ?, ?)
                """,
                (user_id, normalized_email, name.strip(), pw_hash, salt, plan, now, now),
            )
            conn.commit()

        return UserRecord(
            id=user_id,
            email=normalized_email,
            name=name.strip(),
            provider="email",
            plan=plan,
            created_at=now,
            updated_at=now,
        )

    def create_or_update_google_user(
        self,
        *,
        google_id: str,
        email: str,
        name: str,
        avatar_url: Optional[str] = None,
    ) -> UserRecord:
        normalized_email = email.strip().lower()
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            # Check if user with this google_id or email exists
            row = conn.execute(
                "SELECT * FROM users WHERE google_id = ? OR email = ?",
                (google_id, normalized_email),
            ).fetchone()

            if row:
                user_id = row["id"]
                conn.execute(
                    """
                    UPDATE users
                    SET google_id = ?, name = ?, avatar_url = COALESCE(?, avatar_url), updated_at = ?
                    WHERE id = ?
                    """,
                    (google_id, name.strip() or row["name"], avatar_url, now, user_id),
                )
                conn.commit()
                return self.get_user_by_id(user_id)  # type: ignore

            # New user via Google
            user_id = f"usr_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO users (id, email, name, provider, google_id, avatar_url, plan, created_at, updated_at)
                VALUES (?, ?, ?, 'google', ?, ?, 'free', ?, ?)
                """,
                (user_id, normalized_email, name.strip() or "Google User", google_id, avatar_url, now, now),
            )
            conn.commit()

        return UserRecord(
            id=user_id,
            email=normalized_email,
            name=name.strip(),
            provider="google",
            google_id=google_id,
            avatar_url=avatar_url,
            plan="free",
            created_at=now,
            updated_at=now,
        )

    def verify_credentials(self, email: str, password: str) -> Optional[UserRecord]:
        normalized_email = email.strip().lower()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (normalized_email,),
            ).fetchone()

            if not row or not row["password_hash"] or not row["salt"]:
                return None

            computed_hash = self.hash_password(password, row["salt"])
            if hmac.compare_digest(computed_hash, row["password_hash"]):
                return UserRecord(
                    id=row["id"],
                    email=row["email"],
                    name=row["name"],
                    provider=row["provider"],
                    google_id=row["google_id"],
                    avatar_url=row["avatar_url"],
                    plan=row["plan"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserRecord]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                return UserRecord(
                    id=row["id"],
                    email=row["email"],
                    name=row["name"],
                    provider=row["provider"],
                    google_id=row["google_id"],
                    avatar_url=row["avatar_url"],
                    plan=row["plan"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        return None

    def get_user_by_email(self, email: str) -> Optional[UserRecord]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
            if row:
                return UserRecord(
                    id=row["id"],
                    email=row["email"],
                    name=row["name"],
                    provider=row["provider"],
                    google_id=row["google_id"],
                    avatar_url=row["avatar_url"],
                    plan=row["plan"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        return None

    def update_user_profile(
        self,
        user_id: str,
        *,
        name: Optional[str] = None,
        plan: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional[UserRecord]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if not row:
                return None

            new_name = name.strip() if name is not None else row["name"]
            new_plan = plan.strip() if plan is not None else row["plan"]
            new_avatar = avatar_url if avatar_url is not None else row["avatar_url"]

            conn.execute(
                """
                UPDATE users
                SET name = ?, plan = ?, avatar_url = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_name, new_plan, new_avatar, now, user_id),
            )
            conn.commit()

        return self.get_user_by_id(user_id)

    # ─── Session Management ───

    def create_session(self, user_id: str, days_valid: int = 14) -> str:
        token = f"samvad_tok_{secrets.token_urlsafe(32)}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(days=days_valid)).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (token, user_id, now.isoformat(), expires_at),
            )
            conn.commit()

        return token

    def get_user_from_token(self, token: str) -> Optional[UserRecord]:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT u.* FROM users u
                JOIN sessions s ON u.id = s.user_id
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (token, now),
            ).fetchone()

            if row:
                return UserRecord(
                    id=row["id"],
                    email=row["email"],
                    name=row["name"],
                    provider=row["provider"],
                    google_id=row["google_id"],
                    avatar_url=row["avatar_url"],
                    plan=row["plan"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
        return None

    def revoke_session(self, token: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return cursor.rowcount > 0

    # ─── Pro Plan Early Access Waitlist ───

    def add_to_waitlist(
        self,
        email: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> dict[str, Any]:
        normalized = email.strip().lower()
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM pro_waitlist WHERE email = ?", (normalized,)).fetchone()
            if row:
                pos = conn.execute(
                    "SELECT COUNT(*) FROM pro_waitlist WHERE created_at <= ?",
                    (row["created_at"],),
                ).fetchone()[0]
                return {
                    "id": row["id"],
                    "email": row["email"],
                    "name": row["name"],
                    "created_at": row["created_at"],
                    "already_joined": True,
                    "position": pos,
                }

            waitlist_id = f"wtl_{uuid.uuid4().hex[:12]}"
            conn.execute(
                """
                INSERT INTO pro_waitlist (id, email, name, user_id, created_at, notified)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (waitlist_id, normalized, name.strip() if name else None, user_id, now),
            )
            conn.commit()
            pos = conn.execute("SELECT COUNT(*) FROM pro_waitlist").fetchone()[0]

            return {
                "id": waitlist_id,
                "email": normalized,
                "name": name.strip() if name else None,
                "created_at": now,
                "already_joined": False,
                "position": pos,
            }

    def is_on_waitlist(self, email: str) -> bool:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM pro_waitlist WHERE email = ?",
                (email.strip().lower(),),
            ).fetchone()
            return row is not None

    def get_waitlist_count(self) -> int:
        with self._get_connection() as conn:
            return conn.execute("SELECT COUNT(*) FROM pro_waitlist").fetchone()[0]


_auth_store: Optional[AuthStore] = None


def get_auth_store() -> AuthStore:
    global _auth_store
    if _auth_store is None:
        _auth_store = AuthStore()
    return _auth_store
