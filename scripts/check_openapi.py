import urllib.request, json, sys
url = 'http://127.0.0.1:8000/openapi.json'
try:
    data = urllib.request.urlopen(url, timeout=5).read()
    j = json.loads(data)
    paths = j.get('paths', {})
    target = '/api/v1/admin/canciones/lazy/approve-next'
    if target in paths:
        print('FOUND')
    else:
        print('NOT FOUND')
        # print available admin-related paths
        admin_paths = [p for p in paths.keys() if p.startswith('/api/v1/admin')]
        print('\n'.join(admin_paths))
except Exception as e:
    print('ERROR', e)
    sys.exit(2)
