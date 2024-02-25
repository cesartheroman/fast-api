from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Todo(BaseModel):
    id: int
    name: str


sample_todo = Todo(id=1, name="Sample todo")
global_todos: List[Todo] = [sample_todo]


# Get Todos
@app.get("/todos")
async def get_todos():
    return {"todos": global_todos}


# Get Todo by id
@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    for todo in global_todos:
        if todo.id == todo_id:
            return {"todo": todo}

    return {f"'message': 'No  todo of id: {todo_id}'"}


# Create Todo
@app.post("/todos")
async def create_todo(new_todo: Todo):
    global_todos.append(new_todo)

    return {f"'message': 'Todo {new_todo.name} successfully created!'"}


# Update Todo
@app.put("/todos")
async def update_todo(updated_todo: Todo):
    for todo in global_todos:
        if todo.id == updated_todo.id:
            todo.id = updated_todo.id
            todo.name = updated_todo.name

            return {f"'message': Updated todo {updated_todo.name}'"}

    return {f"'message': 'Todo not found'"}


# Delete Todo by id
@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    global global_todos
    updated_todos = filter(lambda todo: todo.id != todo_id, global_todos)
    global_todos[:] = list(updated_todos)

    return {"message": "Todo successfully deleted"}
