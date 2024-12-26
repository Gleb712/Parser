from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Database
from models import Item
from parser import parse_and_save


# Инициализация FastAPI
app = FastAPI()

# Инициализация сессии
session : Session = None


@app.on_event("startup")
async def startup_event():
    # Инициализация базы данных
    global session
    db = Database()
    session = db.Session()
    db.create_db()


# Эндпоинты API
@app.post("/parse/")
async def start_parsing(background_tasks: BackgroundTasks):
    """Парсинг в фоне"""
    background_tasks.add_task(parse_and_save, session)
    return {"message": parse_and_save(session)}


@app.put("/items/{item_id}")
async def update_item(item_id: int, name: str, price: float):
    """Редактирование товара"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    item.name = name
    item.price = price
    session.commit()
    return {"message": "Товар успешно изменен"}


@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Удаление товара"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    session.delete(item)
    session.commit()
    return {"message": "Товар успешно удален"}
