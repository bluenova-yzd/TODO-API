import sqlite3


def get_connection():
    connection = sqlite3.connect("todos.db")
    return connection


def create_table():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        completed BOOLEAN NOT NULL
    )
    """)

    connection.commit()
    connection.close()


def get_all_todos():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, title, completed FROM todos")
    todos = cursor.fetchall()

    connection.close()

    return todos


def create_todo(title, completed):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO todos (title, completed) VALUES (?, ?)",
        (title, completed)
    )

    connection.commit()

    todo_id = cursor.lastrowid

    connection.close()

    return todo_id


def get_todo(todo_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, title, completed FROM todos WHERE id = ?",
        (todo_id,)
    )

    todo = cursor.fetchone()

    connection.close()

    return todo


def update_todo(todo_id, title, completed):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE todos
        SET title = ?, completed = ?
        WHERE id = ?
        """,
        (title, completed, todo_id)
    )

    connection.commit()

    cursor.execute(
        "SELECT id, title, completed FROM todos WHERE id = ?",
        (todo_id,)
    )

    updated_todo = cursor.fetchone()

    connection.close()

    return updated_todo


def delete_todo(todo_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM todos WHERE id = ?",
        (todo_id,)
    )

    todo = cursor.fetchone()

    if not todo:
        connection.close()
        return False

    cursor.execute(
        "DELETE FROM todos WHERE id = ?",
        (todo_id,)
    )

    connection.commit()
    connection.close()

    return True