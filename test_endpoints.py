#!/usr/bin/env python3
"""
Script to test all admin dashboard endpoints and report issues.
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
HEADERS = {"X-API-Key": "test-admin-key"}

# All endpoints used by frontend modules
ENDPOINTS = [
    # Dashboard endpoints
    ("GET", "/admin/summary"),
    ("GET", "/admin/autoplay/status"),
    ("GET", "/admin/recent-consumos?limit=25"),
    ("POST", "/admin/broadcast-message", {"mensaje": "test"}),
    ("POST", "/admin/reset-night"),
    ("POST", "/admin/consumos/{consumo_id}/mark-despachado"),
    ("DELETE", "/admin/consumos/{consumo_id}"),
    
    # Queue endpoints
    ("GET", "/canciones/cola"),
    ("GET", "/mesas/"),
    ("GET", "/youtube/search?q=test"),
    ("POST", "/admin/mesas/{mesa_id}/add-song", {"titulo": "test", "youtube_id": "test", "duracion_seconds": 0}),
    ("POST", "/canciones/{cancion_id}/rechazar"),
    ("POST", "/admin/reorder-queue", {"canciones_ids": []}),
    ("POST", "/admin/canciones/restart"),
    ("POST", "/api/v1/canciones/siguiente"),
    
    # Inventory endpoints
    ("GET", "/productos/"),
    ("POST", "/productos/", {"nombre": "test", "categoria": "test", "valor": 0, "stock": 0}),
    ("POST", "/productos/{product_id}/activate"),
    ("POST", "/productos/{product_id}/deactivate"),
    ("DELETE", "/productos/{product_id}"),
    ("POST", "/productos/{product_id}/upload-image"),
    
    # Tables endpoints
    ("GET", "/mesas/"),
    ("POST", "/mesas/", {"nombre": "test", "qr_code": "test"}),
    ("POST", "/mesas/{mesa_id}/activate"),
    ("POST", "/mesas/{mesa_id}/deactivate"),
    ("DELETE", "/mesas/{mesa_id}"),
    
    # Accounts endpoints (may not exist)
    ("GET", "/consumos/accounts"),
    ("POST", "/consumos/accounts", {"usuario": "test", "comision_percentage": 0}),
    ("POST", "/consumos/accounts/{account_id}/record-payment", {"monto": 0}),
    ("DELETE", "/consumos/accounts/{account_id}"),
    
    # Reports endpoints
    ("GET", "/consumos/report/daily"),
    ("GET", "/consumos/report/weekly"),
    ("GET", "/consumos/report/monthly"),
    ("GET", "/consumos/report/accounts-summary"),
    ("GET", "/consumos/report/top-products"),
    
    # Settings endpoints (may not exist)
    ("GET", "/admin/settings"),
    ("POST", "/admin/settings/closing-time", {"closing_hour": 3, "closing_minute": 0}),
    ("POST", "/admin/settings/api-keys", {"admin_api_key": ""}),
    ("POST", "/admin/settings/general", {"app_name": "test", "theme": "dark"}),
]

def test_endpoint(method, path, body=None):
    """Test a single endpoint and return status code."""
    url = BASE_URL + path if path.startswith("/") else BASE_URL + "/" + path
    # Skip parametrized paths
    if "{" in url:
        return (None, "SKIPPED (parametrized)")
    
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, timeout=5)
        elif method == "POST":
            r = requests.post(url, headers=HEADERS, json=body, timeout=5)
        elif method == "DELETE":
            r = requests.delete(url, headers=HEADERS, timeout=5)
        elif method == "PUT":
            r = requests.put(url, headers=HEADERS, json=body, timeout=5)
        else:
            return (None, "UNKNOWN_METHOD")
        
        return (r.status_code, None)
    except requests.exceptions.Timeout:
        return (None, "TIMEOUT")
    except requests.exceptions.ConnectionError:
        return (None, "CONNECTION_ERROR")
    except Exception as e:
        return (None, str(e)[:50])

def main():
    print("=" * 80)
    print("TESTING ALL FRONTEND ENDPOINTS")
    print("=" * 80)
    
    results = {"ok": [], "4xx": [], "5xx": [], "error": [], "skipped": []}
    
    for method, path, *body_list in ENDPOINTS:
        body = body_list[0] if body_list else None
        status, error = test_endpoint(method, path, body)
        
        endpoint_str = f"{method:6} {path:50}"
        
        if error == "SKIPPED (parametrized)":
            print(f"⊘ {endpoint_str} [SKIPPED]")
            results["skipped"].append(endpoint_str)
        elif error:
            print(f"✗ {endpoint_str} [{error}]")
            results["error"].append(endpoint_str)
        elif status and 200 <= status < 300:
            print(f"✓ {endpoint_str} [{status}]")
            results["ok"].append(endpoint_str)
        elif status and 400 <= status < 500:
            print(f"✗ {endpoint_str} [{status}]")
            results["4xx"].append((endpoint_str, status))
        elif status and status >= 500:
            print(f"✗ {endpoint_str} [{status}]")
            results["5xx"].append((endpoint_str, status))
        else:
            print(f"? {endpoint_str} [UNKNOWN]")
            results["error"].append(endpoint_str)
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✓ Success (2xx):  {len(results['ok'])}")
    print(f"✗ Client (4xx):   {len(results['4xx'])}")
    print(f"✗ Server (5xx):   {len(results['5xx'])}")
    print(f"⚠ Errors:         {len(results['error'])}")
    print(f"⊘ Skipped:        {len(results['skipped'])}")
    
    if results["4xx"]:
        print("\n4xx Errors (likely missing endpoints or validation issues):")
        for endpoint, status in results["4xx"]:
            print(f"  {endpoint} -> {status}")
    
    if results["5xx"]:
        print("\n5xx Errors (server issues):")
        for endpoint, status in results["5xx"]:
            print(f"  {endpoint} -> {status}")
    
    if results["error"]:
        print("\nConnection/Other Errors:")
        for endpoint in results["error"]:
            print(f"  {endpoint}")

if __name__ == "__main__":
    main()
