from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

payload = {'nombre': 'E2E_TC_PRODUCT', 'categoria': 'test', 'valor': 3.5, 'stock': 7}
headers = {'X-API-Key': 'zxc12345'}

resp = client.post('/api/v1/productos/', json=payload, headers=headers)
print('status', resp.status_code)
print('body', resp.json())
