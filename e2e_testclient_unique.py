from fastapi.testclient import TestClient
import main
import time

client = TestClient(main.app)

name = f'E2E_UNIQ_{int(time.time())}'
payload = {'nombre': name, 'categoria': 'test', 'valor': 4.25, 'stock': 3}
headers = {'X-API-Key': 'zxc12345'}

resp = client.post('/api/v1/productos/', json=payload, headers=headers)
print('status', resp.status_code)
print('body', resp.json())
