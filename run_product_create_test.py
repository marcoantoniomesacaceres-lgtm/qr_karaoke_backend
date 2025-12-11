from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

payload = {
    "nombre": "TestProdFromScript",
    "categoria": "Bebidas",
    "valor": 12.5,
    "costo": 5.25,
    "stock": 10
}

resp = client.post("/api/v1/productos/", json=payload, headers={"X-API-Key": "zxc12345"})
try:
    print('STATUS:', resp.status_code)
    try:
        print('JSON:', resp.json())
    except Exception:
        print('RESPONSE TEXT:', resp.text)
except Exception as e:
    print('EXCEPTION:', repr(e))
