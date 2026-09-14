from __future__ import annotations
import asyncio
from websockets.asyncio.server import serve, ServerConnection
import json


connected_clients: set[Client] = set()
alltime_clients: set[Client] = set()
def toJSON(content : str, type : str, author : str, counter : int) -> dict[str, str | int]:
    return {"content": content, "type": type, "author": author, "counter": counter}
log : list[Package] = []
class Package():
    def __init__(self, content : str = "", author : str = "", type : str = "", counter : int = 0):
        self.content = content
        self.author = author
        self.type = type
        self.counter = counter
        

    async def send(self, websocket : ServerConnection) -> None:
        await websocket.send(json.dumps(toJSON(self.content, self.type, self.author, self.counter)))

    @staticmethod
    def receive(message : str | bytes):
        data = json.loads(message)
        return Package(data["content"], data["author"], data["type"], data["counter"])

class Client():
    def __init__(self, websocket : ServerConnection):
        self.websocket = websocket
        self.name = ""
        self.id = str(websocket.remote_address[0]) + str(websocket.remote_address[1])
        connected_clients.add(self)
        self.counter = 0
        self.identified = False

    def delete(self):
        self.identified = False
        connected_clients.remove(self)

    async def identify(self, identification : str):
        infos = identification.split("\n")
        self.name = infos[0].strip()
        self.password = infos[1].strip()
        print(self.name)
        print(self.password)
        for client in alltime_clients:
            if client.name == self.name:
                if client.password != self.password:
                    await self.sendPackage(Package("password", "serveur", "identification"))
                    return 
        alltime_clients.add(self)
        self.identified = True
        print("New user")
        await self.sendPackage(Package("ok", "serveur", "identification"))
        for other in connected_clients:
            if other == self:
                continue
            await self.sendPackage(Package(f"{other.name} est connecté", "serveur", "connection"))
        print(f"{self.id} vient de se connecter")
        await asyncio.gather(*(self.sendPackage(package) for package in log))
        await asyncio.gather(*(client.sendPackage(Package(f"{self.name} vient de se connecter", "serveur", "connection", )) for client in connected_clients))

                

    async def sendPackage(self, package : Package) -> None:
        if package.type == "message" or package.type == "connection":
            self.counter += 1 
            package.counter += 1 
        await package.send(self.websocket)
    
async def echo_handler(websocket : ServerConnection):
    client = Client(websocket)
    print(f"Connection opened: {client.id}")
    await client.sendPackage(Package("PING", "serveur", "ping"))
    print(f"{client.id} <- PING")
    try:
        async for package in client.websocket:
            package = Package.receive(package)
            print(f"{client.id} -> {package.content}")
            if package.type == "identification":
                await client.identify(package.content)
            if package.type == "message":
                print("New message")
                log.append(package)
                await asyncio.gather(*(client.sendPackage(package) for client in connected_clients))
    finally:
        print(f"Connection closed: {client.id}")
        name = client.name
        client.delete()
        await asyncio.gather(*(client.sendPackage(Package(f"{name} vient de se déconnecter", "serveur", "connection")) for client in connected_clients))
        # timer_task.cancel()

async def main():
    async with serve(echo_handler, "localhost", 8765):
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.get_running_loop().create_future()  
if __name__ == "__main__":
    asyncio.run(main())