import asyncio
import sys
import time
import json
import requests

try:
    import websockets
except ImportError:
    print("websockets package not installed. Install with: pip install websockets")
    sys.exit(1)

WS_URL = 'ws://127.0.0.1:8000/ws/cola'
POST_URL = 'http://127.0.0.1:8000/api/v1/productos/'
API_KEY = 'zxc12345'

async def simulate():
    # Open websocket, then close abruptly
    try:
        async with websockets.connect(WS_URL) as ws:
            print('Connected websocket, then closing abruptly...')
            # Terminate the connection without waiting for clean close
            await ws.close(code=1001)
    except Exception as e:
        print('Websocket connect/close raised:', e)

    # Give server a moment to register the closed socket
    time.sleep(0.5)

    payload = {
        'nombre': f'SIM_WS_{int(time.time())}',
        'categoria': 'test',
        'valor': '3.90',
        'stock': 2
    }
    headers = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}
    try:
        r = requests.post(POST_URL, data=json.dumps(payload), headers=headers)
        print('POST status:', r.status_code)
        try:
            print('POST response json:', r.json())
        except Exception:
            print('POST response text:', r.text[:400])
    except Exception as e:
        print('POST request failed:', e)

if __name__ == '__main__':
    asyncio.run(simulate())
