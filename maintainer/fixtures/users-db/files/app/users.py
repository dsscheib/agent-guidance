"""User records."""


def create_user(conn, name, created_at):
    cursor = conn.execute("INSERT INTO users (name, created_at) VALUES (?, ?)", (name, created_at))
    conn.commit()
    return cursor.lastrowid


def get_user(conn, user_id):
    row = conn.execute("SELECT id, name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    return None if row is None else {"id": row[0], "name": row[1], "created_at": row[2]}
