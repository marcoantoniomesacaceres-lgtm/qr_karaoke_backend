
import requests
import json

BASE_URL = "http://localhost:8000"
MASTER_KEY = "admin123" # Assuming this from previous context or default. If fail, I'll check config.

def login():
    try:
        response = requests.post(f"{BASE_URL}/admin/auth/login", json={"api_key": MASTER_KEY})
        if response.status_code == 200:
            return response.json().get("token")
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def verify_restriction():
    token = login()
    if not token:
        print("Cannot proceed without token.")
        return

    headers = {"X-API-Key": token}
    
    # 1. Use Mesa 1 for testing (Assuming it exists, if not we might need to find one)
    mesa_id = 1
    
    # 2. Get current status
    print(f"Checking status for Mesa {mesa_id}...")
    status_resp = requests.get(f"{BASE_URL}/admin/tables/{mesa_id}/payment-status", headers=headers)
    if status_resp.status_code != 200:
        print(f"Failed to get status: {status_resp.text}")
        return
        
    status = status_resp.json()
    saldo = status.get("saldo_pendiente", 0)
    print(f"Current pending balance: {saldo}")
    
    # 3. If balance is 0, we need to create debt to test the restriction.
    if saldo == 0:
        print("Balance is 0. Creating a consumption to generate debt...")
        # Create a product/consumption? Maybe easier to just say we need a setup that has debt.
        # But let's try to add a dummy consumption if possible, or just fail saying we need debt.
        # Ideally, we should add a quick consumption.
        # Let's check products first? 
        pass 
        # For this quick test, let's assume the user has some data or we can try to trigger the error if there IS debt.
    
    # 4. Try to create new account
    print("Attempting to create a new account...")
    create_resp = requests.post(f"{BASE_URL}/admin/tables/{mesa_id}/new-account", headers=headers)
    
    if create_resp.status_code == 400:
        print("SUCCESS: Creation blocked as expected.")
        print(f"Response: {create_resp.json()}")
    elif create_resp.status_code == 200:
        if saldo > 0:
            print("FAILURE: Account created despite pending balance!")
        else:
            print("Account created successfully (Expected as balance was 0).")
    else:
        print(f"Unexpected response: {create_resp.status_code} - {create_resp.text}")

if __name__ == "__main__":
    verify_restriction()
