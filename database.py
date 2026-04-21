import aiosqlite
import os
import json
from datetime import datetime, timezone

DB_PATH = os.getenv("DATABASE_PATH", "concierge.db")


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT '',
                language TEXT DEFAULT 'en',
                preferences TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                payload TEXT DEFAULT '{}',
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
            CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
            CREATE INDEX IF NOT EXISTS idx_analytics_type ON analytics(event_type);
        """)
        await db.commit()
    finally:
        await db.close()


async def get_or_create_user(phone: str) -> dict:
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await db.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        row = await cursor.fetchone()
        if row:
            return dict(row)
        await db.execute(
            "INSERT INTO users (phone, created_at, updated_at) VALUES (?, ?, ?)",
            (phone, now, now),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM users WHERE phone = ?", (phone,))
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await db.close()


async def save_message(user_id: int, role: str, content: str):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO conversations (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_conversation_history(user_id: int, limit: int = 20) -> list[dict]:
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT role, content FROM conversations WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    finally:
        await db.close()


async def update_user_preferences(user_id: int, preferences: dict):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE users SET preferences = ?, updated_at = ? WHERE id = ?",
            (json.dumps(preferences), now, user_id),
        )
        await db.commit()
    finally:
        await db.close()


async def log_analytics(event_type: str, payload: dict | None = None):
    db = await get_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "INSERT INTO analytics (event_type, payload, created_at) VALUES (?, ?, ?)",
            (event_type, json.dumps(payload or {}), now),
        )
        await db.commit()
    finally:
        await db.close()


async def get_dashboard_stats() -> dict:
    db = await get_db()
    try:
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
        total_users = (await cursor.fetchone())["cnt"]

        cursor = await db.execute("SELECT COUNT(*) as cnt FROM conversations")
        total_messages = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM conversations WHERE created_at >= date('now', '-1 day')"
        )
        active_today = (await cursor.fetchone())["cnt"]

        cursor = await db.execute(
            """SELECT event_type, COUNT(*) as cnt FROM analytics
               GROUP BY event_type ORDER BY cnt DESC LIMIT 10"""
        )
        top_events = [dict(r) for r in await cursor.fetchall()]

        cursor = await db.execute(
            """SELECT u.phone, u.name, COUNT(c.id) as msg_count, MAX(c.created_at) as last_active
               FROM users u LEFT JOIN conversations c ON u.id = c.user_id
               GROUP BY u.id ORDER BY last_active DESC LIMIT 20"""
        )
        recent_users = [dict(r) for r in await cursor.fetchall()]

        return {
            "total_users": total_users,
            "total_messages": total_messages,
            "active_today": active_today,
            "top_events": top_events,
            "recent_users": recent_users,
        }
    finally:
        await db.close()
