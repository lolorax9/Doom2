from __future__ import annotations
import asyncio
from websockets.asyncio.server import serve, ServerConnection
import json
log : list[Package] = []
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
        await asyncio.gather(*(client.send(Package(f"{client.name} vient de se déconnecter", "serveur", "connection")) for other in self.connected_clients))
    async def identify(self, identification, connection):
        error = ""
        infos = identification.split("\n")
        name = infos[0].strip()
        password = infos[1].strip()
        fclient = None
        for client in self.clients:
            if client.name == name:
                if client in self.connected_clients:
                    await connection.send(Package("double", "serveur", "identification"))
                    return 
                elif client.password != password:
                    await connection.send(Package("password", "serveur", "identification"))
                    return
                else:
                    fclient = client
        if not fclient:
            fclient = Client(name, password)
            self.clients.add(fclient)
        fclient.connect(connection)
        self.connected_clients.add(fclient)
        await fclient.send(Package("ok", "serveur", "identification"))
        for other in self.connected_clients:
            if other == fclient:
                    continue
            await fclient.send(Package(f"{other.name} est connecté", "serveur", "connection"))
        print(f"{fclient.name} vient de se connecter")
        await asyncio.gather(*(fclient.send(package) for package in log))
        await asyncio.gather(*(client.send(Package(f"{fclient.name} vient de se connecter", "serveur", "connection")) for client in self.connected_clients))
        return fclient

class Package():
    def __init__(self, content : str = "", author : str = "", type : str = ""):
        self.content = content
        self.author = author
        self.type = type
    def toJSON(self):
        return {"content": self.content, "author": self.author, "type": self.type}
    @staticmethod
    def receive(message : str | bytes):
        data = json.loads(message)
        return Package(data["content"], data["author"], data["type"])

class Client():
    def __init__(self, name, password):
        self.name = name
        self.password = password
        self.connection = None
    async def send(self, package):
        if self.connection:
            await self.connection.send(package)
    def connect(self, connection):
        self.connection = connection
    def disconnect(self):
        self.connection = None
        

        

class Connection():
    def __init__(self, websocket):
        self.websocket = websocket
    async def send(self, package):
        await self.websocket.send(json.dumps(package.toJSON()))
    
async def echo_handler(websocket : ServerConnection):
    manager = ConnectionManager()
    connection = Connection(websocket)
    client = None
    print(f"Connection opened: {connection.websocket}")
    await connection.send(Package("PING", "serveur", "ping"))
    print(f"{connection.websocket} <- PING")
    try:
        async for package in connection.websocket:
            package = Package.receive(package)
            print(f"{connection.websocket} -> {package.content}")
            if package.type == "identification":
                client = await manager.identify(package.content, connection)
            elif package.type == "message":
                print("New message")
                log.append(package)
                await asyncio.gather(*(client.send(package) for client in manager.connected_clients))
    finally:
        print(f"Connection closed: {connection.websocket}")
        await manager.disconnect(client)
        

async def main():
    async with serve(echo_handler, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()  
if __name__ == "__main__":
    asyncio.run(main())