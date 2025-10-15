import requests, time, sys, uuid
base='http://127.0.0.1:8000/api/v1'
ADMIN_KEY = 'zxc12345'
try:
    print('Creating mesa...')
    qr = 'ws-test-' + uuid.uuid4().hex[:8]
    m = requests.post(base+'/mesas/', json={'nombre':'Mesa WS Test','qr_code': qr})
    print('mesa status', m.status_code)
    try:
        mj = m.json()
    except Exception:
        print('mesa response non-json', m.text)
        sys.exit(1)
    print('mesa', mj)

    print('Creating usuario...')
    # The public endpoint to connect a user uses the mesa QR code path
    u = requests.post(base+f"/mesas/{mj['qr_code']}/conectar", json={'nick':'ws_user'})
    print('usuario status', u.status_code)
    try:
        uj = u.json()
    except Exception:
        print('usuario response non-json', u.text)
        sys.exit(1)
    print('usuario', uj)

    print('Creating product (may require admin key)...')
    # Create a product using admin API key
    headers = {'X-API-Key': ADMIN_KEY}
    p = requests.post(base+'/productos/', json={'nombre':'Papas de Todito','categoria':'Snacks','valor':10.0,'stock':50}, headers=headers)
    print('producto status', p.status_code)
    try:
        pj = p.json()
    except Exception:
        print('producto response non-json', p.text)
        sys.exit(1)
    print('producto', pj)

    time.sleep(0.5)
    print('Posting consumo...')
    cons = requests.post(base+f'/consumos/pedir/{uj["id"]}', json={'producto_id': pj['id'], 'cantidad': 2})
    print('consumo status', cons.status_code)
    try:
        print(cons.json())
    except Exception as e:
        print('no json', e)
except Exception as e:
    print('error in run_sim:', e)
    raise
