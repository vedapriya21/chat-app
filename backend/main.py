from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import json
from datetime import datetime
from backend.database import get_db, engine
from backend.model import Message, Base

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        message_json = json.dumps(message)
        for connection in self.active_connections:
            await connection.send_text(message_json)

manager = ConnectionManager()

@app.on_event("startup")
async def startup():
    """Create tables at startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
def home():
    return {"message": "Welcome to the Chat API"}

@app.get("/messages")
async def get_messages(db: AsyncSession = Depends(get_db)):
    """Retrieve all messages from the database."""
    try:
        result = await db.execute(select(Message))
        messages = result.scalars().all()
        return {"messages": [msg.to_dict() for msg in messages]}
    except Exception as e:
        return {"error": str(e)}

@app.post("/messages")
async def send_message(data: dict, db: AsyncSession = Depends(get_db)):
    """Store a new message in the database and broadcast it."""
    try:
        now = datetime.now().strftime("%H:%M")
        message = Message(time=now, client_id=data["client_id"], content=data["message"])
        db.add(message)
        await db.commit()
        await db.refresh(message)
        
        message_dict = message.to_dict()
        await manager.broadcast(message_dict)
        return {"status": "Message sent", "message": message_dict}
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int, db: AsyncSession = Depends(get_db)):
    """WebSocket connection for real-time messaging."""
    print(f"🔵 Client {client_id} is attempting to connect...")
    await manager.connect(websocket)
    print(f"✅ Client {client_id} connected!")

    try:
        while True:
            data = await websocket.receive_text()
            now = datetime.now().strftime("%H:%M")
            
            message = Message(time=now, client_id=client_id, content=data)
            db.add(message)
            await db.commit()
            await db.refresh(message)
            
            message_dict = message.to_dict()
            print(f"Received message: {message_dict}")
            await manager.broadcast(message_dict)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {client_id} disconnected!")
        
        disconnect_message = {"time": now, "client_id": client_id, "message": "Client disconnected"}
        await manager.broadcast(disconnect_message)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")