from fastapi import FastAPI, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from database import Database
from models import Item
from parser import parse_and_save
from typing import List


# Список клиентов подключенных через WebSocket
connected_clients: list[WebSocket] = []

# Управление подключениями WebSocket
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

# Функция для парсинга и отправки уведомлений через WebSocket
async def parse_and_notify():
    parse_and_save(session) # Запускает парсинг и сохраняет данные в базу данных
    await manager.send_message("Данные успешно обновлены!")

# Планировщик для автоматического запуска парсера каждый час
scheduler = BackgroundScheduler()
scheduler.add_job(parse_and_notify, 'interval', hours=1)
scheduler.start()

# Создает подключение к базе данных и вызывает метод создания таблиц
@app.on_event("startup")
async def startup_event():
    global session
    db = Database()
    session = db.Session()
    db.create_db()

# Закрывает планировщик и отключает базу данных
@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    session.close()

@app.post("/parse/")
async def start_parsing(background_tasks: BackgroundTasks):
    """Парсинг в фоне"""
    background_tasks.add_task(parse_and_notify)

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    """Получение данных о товаре по ID"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    # Уведомляем подключенных клиентов через WebSocket
    await manager.send_message(f"Данные о товаре с ID {item_id} получены.")
    return {"id": item.id, "name": item.name, "price": item.price}

@app.put("/items/{item_id}")
async def update_item(item_id: int, name: str, price: float):
    """Редактирование товара"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    item.name = name
    item.price = price
    session.commit()
    # Уведомляем подключенных клиентов через WebSocket
    await manager.send_message(f"Товар с ID {item_id} изменен.")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Удаление товара"""
    item = session.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    session.delete(item)
    session.commit()
    # Уведомляем подключенных клиентов через WebSocket
    await manager.send_message(f"Товар с ID {item_id} удален.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Эндпоинт для WebSocket соединений"""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def get():
    """Возвращает HTML-страницу с клиентом для WebSocket и отображает входящие сообщения"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Client</title>
    </head>
    <body>
        <h1>WebSocket Уведомления</h1>
        <div id="messages"></div>
        <script>
            const ws = new WebSocket("ws://localhost:8000/ws");
            const messagesDiv = document.getElementById("messages");

            ws.onmessage = function(event) {
                const message = document.createElement("div");
                message.textContent = event.data;
                messagesDiv.appendChild(message);
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
