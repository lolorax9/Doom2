from __future__ import annotations
import asyncio
from websockets.asyncio.server import serve, ServerConnection
import json
log : list[Message] = []
class ConnectionManager():
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):
        if not self._initialized: 
            self.connected_clients = set()
            self.clients = set()
            self._initialized = True
    async def disconnect(self, client):
        client.disconnect()
        del client.connection
        self.connected_clients.remove(client)
        await asyncio.gather(*(other.send(Message("connection", {"author" : "serveur", "chat" : f"{client.name} vient de se déconnecter"})) for other in self.connected_clients))
    async def identify(self, payload, connection):
        name = payload["name"].strip()
        password = payload["password"].strip()
        fclient = None
        for client in self.clients:
            if client.name == name:
                if client in self.connected_clients:
                    await connection.send(Message("error", {"exception" : "double"}))
                    return 
                elif client.password != password:
                    await connection.send(Message( "error", {"exception" : "password"}))
                    return
                else:
                    fclient = client
        if not fclient:
            fclient = Client(name, password)
            self.clients.add(fclient)
        fclient.connect(connection)
        self.connected_clients.add(fclient)
        await fclient.send(Message("identification", {"name" : fclient.name, "password" : fclient.password}))
        for other in self.connected_clients:
            if other == fclient:
                    continue
            await fclient.send(Message("connection", {"author": "serveur", "chat": f"{other.name} est connecté"}))
        print(f"{fclient.name} vient de se connecter")
        await asyncio.gather(*(fclient.send(message) for message in log))
        await asyncio.gather(*(client.send(Message("connection", {"author":"serveur", "chat" :f"{fclient.name} vient de se connecter"})) for client in self.connected_clients))
        return fclient

class Message():
    def __init__(self,type : str = "", payload : dict | str = {}):
        self.payload = payload
        self.type = type
    def toJSON(self):
        return {"type": self.type, "payload": self.payload}
    @staticmethod
    def receive(message : str | bytes):
        data = json.loads(message)
        return Message(data["type"], data["payload"])

class Client():
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.connection = None
    async def send(self, message):
        if self.connection:
            await self.connection.send(message)
    def connect(self, connection):
        self.connection = connection
        self.connection.client = self
    def disconnect(self):
        self.connection = None
        

        

class Connection():
    def __init__(self, websocket):
        self.websocket = websocket
        self.client = None
    async def send(self, message):
        await self.websocket.send(json.dumps(message.toJSON()))
    
async def echo_handler(websocket : ServerConnection):
    manager = ConnectionManager()
    connection = Connection(websocket)
    client = None
    print(f"Connection opened: {connection.websocket}")
    await connection.send(Message("ping", "PING"))
    print(f"{connection.websocket} <- PING")
    try:
        async for message in connection.websocket:
            message = Message.receive(message)
            print(f"{connection.websocket} -> {message.payload}")
            if message.type == "identification":
                client = await manager.identify(message.payload, connection)
            elif message.type == "chat":
                print("New message")
                log.append(message)
                await asyncio.gather(*(client.send(message) for client in manager.connected_clients))
    finally:
        print(f"Connection closed: {connection.websocket}")
        if client:
            await manager.disconnect(client)
        

async def main():
    async with serve(echo_handler, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()  
if __name__ == "__main__":
    asyncio.run(main())