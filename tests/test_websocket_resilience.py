import asyncio
import time
from fastapi.testclient import TestClient

import main
import websocket_manager


class BrokenWebSocket:
    def __init__(self):
        self.closed = False

    async def send_text(self, data: str):
        # Simulate a connection that raises when sending
        raise RuntimeError("simulated send error")

    async def close(self):
        self.closed = True


def test_create_product_with_broken_websocket(tmp_path):
    client = TestClient(main.app)

    # Inject a broken websocket into the manager
    broken = BrokenWebSocket()
    websocket_manager.manager.active_connections.append(broken)

    # Create a unique product name to avoid collisions
    name = f"TEST_WS_{int(time.time())}"
    payload = {
        "nombre": name,
        "categoria": "test",
        "valor": "1.23",
        "stock": 5
    }

    headers = {"X-API-Key": "zxc12345", "Content-Type": "application/json"}
    resp = client.post("/api/v1/productos/", json=payload, headers=headers)

    # Should succeed despite the broken websocket
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["nombre"] == name

    # The broken connection should have been removed from the active list
    assert broken not in websocket_manager.manager.active_connections
