from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import (
    get_connection,
    create_table,
    get_all_todos,
    create_todo,
    get_todo,
    update_todo,
    delete_todo
)

app = FastAPI()
# Git değişiklik testi

create_table()


class Todo(BaseModel):
    title: str
    completed: bool


@app.get("/")
def ana_sayfa():
    return {"mesaj": "To-Do API çalışıyor!"}


@app.post("/todos")
def create_todo_api(todo: Todo):
    todo_id = create_todo(todo.title, todo.completed)

    return {
        "id": todo_id,
        "title": todo.title,
        "completed": todo.completed
    }


@app.get("/todos")
def get_todos():
    todos = get_all_todos()

    return [
        {
            "id": todo[0],
            "title": todo[1],
            "completed": bool(todo[2])
        }
        for todo in todos
    ]


@app.get("/todos/{todo_id}")
def get_todo_api(todo_id: int):
    todo = get_todo(todo_id)

    if not todo:
        raise HTTPException(
            status_code=404,
            detail="To-Do bulunamadı"
        )

    return {
        "id": todo[0],
        "title": todo[1],
        "completed": bool(todo[2])
    }


@app.put("/todos/{todo_id}")
def update_todo_api(todo_id: int, todo: Todo):
    updated_todo = update_todo(
        todo_id,
        todo.title,
        todo.completed
    )

    if not updated_todo:
        raise HTTPException(
            status_code=404,
            detail="To-Do bulunamadı"
        )

    return {
        "id": updated_todo[0],
        "title": updated_todo[1],
        "completed": bool(updated_todo[2])
    }


@app.delete("/todos/{todo_id}")
def delete_todo_api(todo_id: int):
    deleted = delete_todo(todo_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="To-Do bulunamadı"
        )

    return {"mesaj": "To-Do silindi"}