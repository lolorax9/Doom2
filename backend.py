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
        await asyncio.gather(*(other.send(Message(f"{client.name} vient de se déconnecter", "serveur", "connection")) for other in self.connected_clients))
    async def identify(self, identification, connection):
        error = ""
        infos = identification.split("\n")
        name = infos[0].strip()
        password = infos[1].strip()
        fclient = None
        for client in self.clients:
            if client.name == name:
                if client in self.connected_clients:
                    await connection.send(Message("double", "serveur", "identification"))
                    return 
                elif client.password != password:
                    await connection.send(Message("password", "serveur", "identification"))
                    return
                else:
                    fclient = client
        if not fclient:
            fclient = Client(name, password)
            self.clients.add(fclient)
        fclient.connect(connection)
        self.connected_clients.add(fclient)
        await fclient.send(Message("ok", "serveur", "identification"))
        for other in self.connected_clients:
            if other == fclient:
                    continue
            await fclient.send(Message(f"{other.name} est connecté", "serveur", "connection"))
        print(f"{fclient.name} vient de se connecter")
        await asyncio.gather(*(fclient.send(message) for message in log))
        await asyncio.gather(*(client.send(Message(f"{fclient.name} vient de se connecter", "serveur", "connection")) for client in self.connected_clients))
        return fclient

class Message():
    def __init__(self, payload : str = "", author : str = "", type : str = ""):
        self.payload = payload
        self.author = author
        self.type = type
    def toJSON(self):
        return {"payload": self.payload, "author": self.author, "type": self.type}
    @staticmethod
    def receive(message : str | bytes):
        data = json.loads(message)
        return Message(data["payload"], data["author"], data["type"])

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
    def disconnect(self):
        self.connection = None
        

        

class Connection():
    def __init__(self, websocket):
        self.websocket = websocket
    async def send(self, message):
        await self.websocket.send(json.dumps(message.toJSON()))
    
async def echo_handler(websocket : ServerConnection):
    manager = ConnectionManager()
    connection = Connection(websocket)
    client = None
    print(f"Connection opened: {connection.websocket}")
    await connection.send(Message("PING", "serveur", "ping"))
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