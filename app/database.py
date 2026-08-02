import sqlite3
from pathlib import Path

BASE_DIR = Path("/opt/cpit-signage")
DATABASE_PATH = BASE_DIR / "config" / "signage.db"
MEDIA_DIR = BASE_DIR / "media"

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def get_connection():
    """Open a connection with rows accessible by column name."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create the database tables if they do not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                media_type TEXT NOT NULL DEFAULT 'image',
                duration INTEGER NOT NULL DEFAULT 10,
                sort_order INTEGER NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def import_existing_media():
    """Add supported files from the media directory to SQLite."""
    initialize_database()
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(
        file
        for file in MEDIA_DIR.iterdir()
        if file.is_file() and file.suffix.lower() in SUPPORTED_IMAGES
    )

    with get_connection() as connection:
        existing_count = connection.execute(
            "SELECT COUNT(*) FROM media"
        ).fetchone()[0]

        for offset, file in enumerate(files, start=1):
            connection.execute(
                """
                INSERT OR IGNORE INTO media
                    (filename, media_type, duration, sort_order, enabled)
                VALUES
                    (?, 'image', 10, ?, 1)
                """,
                (file.name, existing_count + offset),
            )


def get_enabled_slides():
    """Return enabled media in playlist order."""
    initialize_database()

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                id,
                filename,
                media_type,
                duration,
                sort_order
            FROM media
            WHERE enabled = 1
            ORDER BY sort_order ASC, id ASC
            """
        ).fetchall()
