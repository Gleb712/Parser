from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from database import Database
from models import Item
from parser import parse_and_save
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# Инициализация FastAPI
app = FastAPI()

# Инициализация соединений WebSocket
manager = ConnectionManager()

# Инициализация базы данных
session: Session = None

@app.on_event("startup")
async def startup_event():
    global session
    db = Database()
    session = db.Session()
    db.create_db()

    # Планировщик для автоматического запуска парсера каждый час
    scheduler = BackgroundScheduler()
    scheduler.add_job(parse_and_notify, 'interval', hours=1)
    scheduler.start()

async def parse_and_notify():
    """Функция для парсинга и отправки уведомлений через WebSocket"""
    parse_and_save(session)
    await manager.send_message("Данные успешно обновлены!")

@app.post("/parse/")
async def start_parsing(background_tasks: BackgroundTasks):
    """Парсинг в фоне"""
    background_tasks.add_task(parse_and_notify)
    return {"message": "Парсинг запущен."}

@app.put("/items/{item_id}")
async def update_item(item_id: int, name: str, price: float):
    """Редактирование товара"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    item.name = name
    item.price = price
    session.commit()
    await manager.send_message(f"Товар с ID {item_id} обновлен.")
    return {"message": "Товар успешно изменен"}

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Удаление товара"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    session.delete(item)
    session.commit()
    await manager.send_message(f"Товар с ID {item_id} удален.")
    return {"message": "Товар успешно удален"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Эндпоинт для WebSocket соединений"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
