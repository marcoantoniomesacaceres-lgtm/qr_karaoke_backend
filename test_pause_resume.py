import requests
import time

BASE_URL = "http://localhost:8000"

def test_pause_resume():
    headers = {"X-API-Key": "zxc12345"}
    print("Testing Pause...")
    r = requests.post(f"{BASE_URL}/api/v1/admin/player/pause", headers=headers)
    if r.status_code == 200:
        print("Pause OK")
    else:
        print(f"Pause Failed: {r.status_code} {r.text}")

    print("Waiting 2 seconds...")
    time.sleep(2)

    print("Testing Resume...")
    r = requests.post(f"{BASE_URL}/api/v1/admin/player/resume", headers=headers)
    if r.status_code == 200:
        print("Resume OK")
    else:
        print(f"Resume Failed: {r.status_code} {r.text}")

if __name__ == "__main__":
    test_pause_resume()
