import json
import urllib.request
import urllib.error

url = 'http://127.0.0.1:8000/api/v1/productos/'
headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'zxc12345'
}

payload = {
    'nombre': 'E2E_TEST_PRODUCT_001',
    'categoria': 'test_e2e',
    'valor': 5.50,
    'stock': 10
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode('utf-8')
        print('STATUS', resp.status)
        print('BODY', body)
except urllib.error.HTTPError as he:
    try:
        body = he.read().decode('utf-8')
    except Exception:
        body = '<no body>'
    print('HTTPError', he.code, body)
except Exception as e:
    print('ERROR', e)
