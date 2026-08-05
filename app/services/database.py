import sqlite3
from pathlib import Path

BASE_DIR = Path("/opt/cpit-signage")
DATABASE_PATH = BASE_DIR / "config" / "signage.db"
MEDIA_DIR = BASE_DIR / "media"

SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

ASSET_TYPE_PLAYLIST = "playlist"
ASSET_TYPE_BACKGROUND = "background"

SUPPORTED_ASSET_TYPES = {
    ASSET_TYPE_PLAYLIST,
    ASSET_TYPE_BACKGROUND,
}


def get_connection():
    """Open a connection with rows accessible by column name."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """
    Create the database and apply compatible schema migrations.

    Existing installations receive the asset_type column automatically.
    Existing media defaults to playlist so current playback behavior is
    preserved during the Step 2A migration.
    """
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                media_type TEXT NOT NULL DEFAULT 'image',
                asset_type TEXT NOT NULL DEFAULT 'playlist',
                duration INTEGER NOT NULL DEFAULT 10,
                sort_order INTEGER NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(media)"
            ).fetchall()
        }

        if "asset_type" not in columns:
            connection.execute(
                """
                ALTER TABLE media
                ADD COLUMN asset_type TEXT NOT NULL DEFAULT 'playlist'
                """
            )

        connection.execute(
            """
            UPDATE media
            SET asset_type = ?
            WHERE
                asset_type IS NULL
                OR TRIM(asset_type) = ''
                OR asset_type NOT IN (?, ?)
            """,
            (
                ASSET_TYPE_PLAYLIST,
                ASSET_TYPE_PLAYLIST,
                ASSET_TYPE_BACKGROUND,
            ),
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
                INSERT OR IGNORE INTO media (
                    filename,
                    media_type,
                    asset_type,
                    duration,
                    sort_order,
                    enabled
                )
                VALUES
                    (?, 'image', 'playlist', 10, ?, 1)
                """,
                (file.name, existing_count + offset),
            )


def get_enabled_slides():
    """Return enabled playlist media in playback order."""
    initialize_database()

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                id,
                filename,
                media_type,
                asset_type,
                duration,
                sort_order
            FROM media
            WHERE
                enabled = 1
                AND asset_type = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (ASSET_TYPE_PLAYLIST,),
        ).fetchall()


def get_all_media():
    """Return all media records, including disabled items."""
    initialize_database()

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                id,
                filename,
                media_type,
                asset_type,
                duration,
                sort_order,
                enabled,
                created_at
            FROM media
            ORDER BY sort_order ASC, id ASC
            """
        ).fetchall()


def get_media_by_asset_type(asset_type: str):
    """Return all media records for one supported asset type."""
    initialize_database()

    normalized_asset_type = str(asset_type).strip().lower()

    if normalized_asset_type not in SUPPORTED_ASSET_TYPES:
        raise ValueError(
            "Asset type must be playlist or background"
        )

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                id,
                filename,
                media_type,
                asset_type,
                duration,
                sort_order,
                enabled,
                created_at
            FROM media
            WHERE asset_type = ?
            ORDER BY sort_order ASC, id ASC
            """,
            (normalized_asset_type,),
        ).fetchall()


def update_media_asset_type(
    media_id: int,
    asset_type: str,
):
    """Move one media item between supported asset libraries."""
    initialize_database()

    normalized_asset_type = str(asset_type).strip().lower()

    if normalized_asset_type not in SUPPORTED_ASSET_TYPES:
        raise ValueError(
            "Asset type must be playlist or background"
        )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE media
            SET asset_type = ?
            WHERE id = ?
            """,
            (normalized_asset_type, media_id),
        )

        return cursor.rowcount > 0


def update_media_item(
    media_id: int,
    duration: int,
    sort_order: int,
    enabled: bool,
):
    """Update editable settings for one media record."""
    initialize_database()

    duration = max(1, min(int(duration), 3600))
    sort_order = max(0, int(sort_order))
    enabled_value = 1 if enabled else 0

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE media
            SET
                duration = ?,
                sort_order = ?,
                enabled = ?
            WHERE id = ?
            """,
            (
                duration,
                sort_order,
                enabled_value,
                media_id,
            ),
        )


def get_media_item(media_id: int):
    """Return one media record by ID, or None if it does not exist."""
    initialize_database()

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                id,
                filename,
                media_type,
                asset_type,
                duration,
                sort_order,
                enabled,
                created_at
            FROM media
            WHERE id = ?
            """,
            (media_id,),
        ).fetchone()


def delete_media_item(media_id: int):
    """Delete one media database record and return whether it existed."""
    initialize_database()

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM media WHERE id = ?",
            (media_id,),
        )

        return cursor.rowcount > 0


def create_media_item(
    filename: str,
    media_type: str = "image",
    asset_type: str = ASSET_TYPE_PLAYLIST,
    duration: int = 10,
    enabled: bool = True,
):
    """Insert a new media record and return the created row."""
    initialize_database()

    duration = max(1, min(int(duration), 3600))
    enabled_value = 1 if enabled else 0

    normalized_asset_type = str(asset_type).strip().lower()

    if normalized_asset_type not in SUPPORTED_ASSET_TYPES:
        raise ValueError(
            "Asset type must be playlist or background"
        )

    with get_connection() as connection:
        next_sort_order = connection.execute(
            """
            SELECT COALESCE(MAX(sort_order), 0) + 1
            FROM media
            """
        ).fetchone()[0]

        cursor = connection.execute(
            """
            INSERT INTO media (
                filename,
                media_type,
                asset_type,
                duration,
                sort_order,
                enabled
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                media_type,
                normalized_asset_type,
                duration,
                next_sort_order,
                enabled_value,
            ),
        )

        media_id = cursor.lastrowid

        return connection.execute(
            """
            SELECT
                id,
                filename,
                media_type,
                asset_type,
                duration,
                sort_order,
                enabled,
                created_at
            FROM media
            WHERE id = ?
            """,
            (media_id,),
        ).fetchone()


def reorder_media_items(media_ids):
    """Update playlist order from an ordered list of media IDs."""
    initialize_database()

    with get_connection() as connection:
        existing_ids = {
            row["id"]
            for row in connection.execute(
                """
                SELECT id
                FROM media
                WHERE asset_type = ?
                """,
                (ASSET_TYPE_PLAYLIST,),
            ).fetchall()
        }

        requested_ids = [int(media_id) for media_id in media_ids]

        if len(requested_ids) != len(set(requested_ids)):
            raise ValueError("Duplicate media IDs are not allowed")

        if set(requested_ids) != existing_ids:
            raise ValueError(
                "The reorder list must include every playlist item exactly once"
            )

        for sort_order, media_id in enumerate(requested_ids, start=1):
            connection.execute(
                """
                UPDATE media
                SET sort_order = ?
                WHERE id = ?
                """,
                (sort_order, media_id),
            )
