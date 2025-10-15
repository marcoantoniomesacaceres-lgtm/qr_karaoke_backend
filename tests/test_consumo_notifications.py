import pytest
from fastapi.testclient import TestClient
import main, crud, models
from database import SessionLocal, engine
import websocket_manager
import asyncio

client = TestClient(main.app)

@pytest.fixture(autouse=True)
def clean_db():
    # For tests, we will recreate tables and start fresh
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield


def test_pedir_triggers_consumo_created(monkeypatch):
    called = {'created': False}

    async def fake_broadcast_consumo_created(payload):
        called['created'] = True
        return 0

    # Replace the manager method
    monkeypatch.setattr(websocket_manager.manager, 'broadcast_consumo_created', fake_broadcast_consumo_created)

    # Also force create_task to run immediately for test determinism
    orig_create_task = asyncio.create_task

    def run_now(coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    monkeypatch.setattr(asyncio, 'create_task', run_now)

    # Create mesa, usuario, producto via API
    r = client.post('/api/v1/mesas/', json={'nombre':'T1','qr_code':'t1'})
    assert r.status_code == 201
    mesa = r.json()

    r = client.post(f"/api/v1/mesas/{mesa['id']}/usuarios", json={'nick':'testuser'})
    assert r.status_code == 201
    usuario = r.json()

    r = client.post('/api/v1/productos/', json={'nombre':'P1','categoria':'Snacks','valor':5.0,'stock':10})
    assert r.status_code == 201
    producto = r.json()

    # Make the pedido
    r = client.post(f"/api/v1/consumos/pedir/{usuario['id']}", json={'producto_id': producto['id'], 'cantidad': 1})
    assert r.status_code == 200
    assert called['created'] is True

    # restore
    monkeypatch.setattr(asyncio, 'create_task', orig_create_task)


def test_admin_delete_triggers_consumo_deleted(monkeypatch):
    called = {'deleted': False}

    async def fake_broadcast_consumo_deleted(consumo_id):
        called['deleted'] = consumo_id
        return 0

    monkeypatch.setattr(websocket_manager.manager, 'broadcast_consumo_deleted', fake_broadcast_consumo_deleted)

    # bypass auth by using MASTER_API_KEY header
    headers = {'X-API-Key': 'zxc12345'}

    # Create mesa, usuario, producto and consumo first
    r = client.post('/api/v1/mesas/', json={'nombre':'T2','qr_code':'t2'})
    mesa = r.json()
    r = client.post(f"/api/v1/mesas/{mesa['id']}/usuarios", json={'nick':'testuser2'})
    usuario = r.json()
    r = client.post('/api/v1/productos/', json={'nombre':'P2','categoria':'Snacks','valor':7.0,'stock':5})
    producto = r.json()

    r = client.post(f"/api/v1/consumos/pedir/{usuario['id']}", json={'producto_id': producto['id'], 'cantidad': 1})
    consumo = r.json()

    # Now delete as admin
    r = client.delete(f"/api/v1/admin/consumos/{consumo['id']}", headers=headers)
    assert r.status_code == 204
    assert called['deleted'] == consumo['id']
