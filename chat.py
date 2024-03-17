import asyncio
import datetime
import logging
import re

import aiofiles
import names
import websockets
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

from main import pb_ex, change_base_currency

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            await self.send_to_clients(f"{ws.name}: {message}")

            if 'exchange' in message:
                await self.log_exchange_command(message)
                curr = change_base_currency()
                match = re.search(r"exchange\s*(10|[1-9])", message)
                days_from = int(match.group(1))
                m = await pb_ex(days_from, curr, 2)
                await self.send_to_clients(f"PrivatBank: {m}")

    async def log_exchange_command(self, message, log_file_path="exchange_log.txt"):
        async with aiofiles.open(log_file_path, mode='a') as log_file:
            time = datetime.datetime.now()
            await log_file.write(f"{time}: {message}\n")

    async def check_messages(self, ws: WebSocketServerProtocol):
        for message in ws:
            await self.log_exchange_command(message)


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever


if __name__ == '__main__':
    asyncio.run(main())
