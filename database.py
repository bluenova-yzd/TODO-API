import sqlite3


def get_connection():
    connection = sqlite3.connect("todos.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed BOOLEAN NOT NULL
    )
    """)

    cursor.execute("PRAGMA table_info(todos)")
    columns = [column[1] for column in cursor.fetchall()]

    if "user_id" not in columns:
        cursor.execute(
            "ALTER TABLE todos ADD COLUMN user_id INTEGER"
        )

    connection.commit()
    connection.close()


def create_user(username, password_hash):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, password_hash)
            VALUES (?, ?)
            """,
            (username, password_hash)
        )

        connection.commit()
        user_id = cursor.lastrowid

        return user_id

    except sqlite3.IntegrityError:
        return None

    finally:
        connection.close()


def get_user_by_username(username):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, username, password_hash
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    user = cursor.fetchone()

    connection.close()

    return user


def get_all_todos(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, completed
        FROM todos
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    )

    todos = cursor.fetchall()

    connection.close()

    return todos


def create_todo(title, completed, user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO todos (title, completed, user_id)
        VALUES (?, ?, ?)
        """,
        (title, completed, user_id)
    )

    connection.commit()

    todo_id = cursor.lastrowid

    connection.close()

    return todo_id


def get_todo(todo_id, user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, title, completed
        FROM todos
        WHERE id = ? AND user_id = ?
        """,
        (todo_id, user_id)
    )

    todo = cursor.fetchone()

    connection.close()

    return todo


def update_todo(todo_id, title, completed, user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE todos
        SET title = ?, completed = ?
        WHERE id = ? AND user_id = ?
        """,
        (title, completed, todo_id, user_id)
    )

    connection.commit()

    cursor.execute(
        """
        SELECT id, title, completed
        FROM todos
        WHERE id = ? AND user_id = ?
        """,
        (todo_id, user_id)
    )

    updated_todo = cursor.fetchone()

    connection.close()

    return updated_todo


def delete_todo(todo_id, user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM todos
        WHERE id = ? AND user_id = ?
        """,
        (todo_id, user_id)
    )

    todo = cursor.fetchone()

    if not todo:
        connection.close()
        return False

    cursor.execute(
        """
        DELETE FROM todos
        WHERE id = ? AND user_id = ?
        """,
        (todo_id, user_id)
    )

    connection.commit()
    connection.close()

    return True