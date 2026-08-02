from app.services.database import (
    DATABASE_PATH,
    get_connection,
    import_existing_media,
)


def main():
    import_existing_media()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, filename, duration, sort_order, enabled
            FROM media
            ORDER BY sort_order, id
            """
        ).fetchall()

    print(f"Database: {DATABASE_PATH}")
    print(f"Imported media records: {len(rows)}")

    for row in rows:
        print(
            f"{row['id']}: {row['filename']} "
            f"(duration={row['duration']}, "
            f"order={row['sort_order']}, "
            f"enabled={row['enabled']})"
        )


if __name__ == "__main__":
    main()
