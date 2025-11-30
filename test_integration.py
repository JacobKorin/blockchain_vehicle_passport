import requests
import json
import sys
import time

# Configuration
BASE_URL = "http://127.0.0.1:5001"
HEADERS = {'Content-Type': 'application/json'}

# ANSI Colors for pretty output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log(message, type="INFO"):
    if type == "INFO":
        print(f"{Colors.OKBLUE}[INFO] {message}{Colors.ENDC}")
    elif type == "PASS":
        print(f"{Colors.OKGREEN}[PASS] {message}{Colors.ENDC}")
    elif type == "FAIL":
        print(f"{Colors.FAIL}[FAIL] {message}{Colors.ENDC}")
    elif type == "HEADER":
        print(f"\n{Colors.HEADER}=== {message} ==={Colors.ENDC}")

def run_test(name, function):
    log(f"Starting Test: {name}", "HEADER")
    try:
        function()
    except AssertionError as e:
        log(f"Assertion Failed: {e}", "FAIL")
    except Exception as e:
        log(f"Error: {e}", "FAIL")

# helper functions for API interactions

def login(role, user_id):
    url = f"{BASE_URL}/api/session/set"
    data = {'role': role, 'user_id': user_id}
    response = requests.post(url, json=data, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    # Save cookies for subsequent requests
    return response.cookies

def register_vehicle(cookies, vin):
    url = f"{BASE_URL}/api/vehicle/register"
    data = {
        'vin': vin, 'make': 'TestMake', 'model': 'TestModel', 
        'year': 2024, 'initial_mileage': 100
    }
    return requests.post(url, json=data, headers=HEADERS, cookies=cookies)

#test cases for full userflow cycle

def test_full_lifecycle():
    VIN = "TEST-LIFECYCLE-001"
    
    # 1. Register
    log("Step 1: Manufacturer registers vehicle")
    cookies = login('MANUFACTURER', 'manufacturer_1')
    res = register_vehicle(cookies, VIN)
    assert res.status_code == 200, f"Registration failed: {res.text}"
    log("Vehicle Registered", "PASS")

    # 2. update mileage
    log("Step 2: Mechanic updates mileage")
    cookies = login('MECHANIC', 'mechanic_1')
    res = requests.post(f"{BASE_URL}/api/vehicle/mileage", 
                        json={'vin': VIN, 'new_mileage': 500}, 
                        cookies=cookies, headers=HEADERS)
    assert res.status_code == 200, "Mileage update failed"
    log("Mileage Updated to 500", "PASS")

    # 3.Service record
    log("Step 3: Mechanic adds service")
    res = requests.post(f"{BASE_URL}/api/vehicle/service",
                        json={'vin': VIN, 'service_type': 'Oil Change'},
                        cookies=cookies, headers=HEADERS)
    assert res.status_code == 200, "Service add failed"
    log("Service Record Added", "PASS")

    # 4. Transfer Ownership
    log("Step 4: Manufacturer transfers to Buyer")
    cookies = login('MANUFACTURER', 'manufacturer_1')
    res = requests.post(f"{BASE_URL}/api/vehicle/transfer",
                        json={'vin': VIN, 'new_owner_id': 'buyer_1'},
                        cookies=cookies, headers=HEADERS)
    assert res.status_code == 200, "Transfer failed"
    log("Ownership Transferred", "PASS")

    # 5. Validate History
    log("Step 5: Verifying history")
    res = requests.get(f"{BASE_URL}/api/vehicle/{VIN}")
    history = res.json()['history']
    assert len(history) == 4, f"Expected 4 transactions, found {len(history)}"
    log("History Verified", "PASS")

#ensuring fraudulent odometer settings are caught
def test_security_checks():
    VIN = "TEST-SEC-001"
    
    # Setup vehicle
    cookies = login('MANUFACTURER', 'manufacturer_1')
    register_vehicle(cookies, VIN)
    
    # 1. Test Mileage Rollback
    log("Security Test 1: Mileage Rollback")
    cookies = login('MECHANIC', 'mechanic_1')
    # Set to 1000 first
    requests.post(f"{BASE_URL}/api/vehicle/mileage", 
                 json={'vin': VIN, 'new_mileage': 1000}, cookies=cookies, headers=HEADERS)
    
    # Try to set to 500 (Fraud)
    res = requests.post(f"{BASE_URL}/api/vehicle/mileage", 
                       json={'vin': VIN, 'new_mileage': 500}, cookies=cookies, headers=HEADERS)
    
    if res.status_code == 400:
        log("System correctly rejected rollback attempt", "PASS")
    else:
        log(f"FAILED: System allowed rollback! Code: {res.status_code}", "FAIL")

    # 2. Test Permission Denied
    log("Security Test 2: Unauthorized Action")
    cookies = login('BUYER', 'buyer_1') # because buyers can't add service records
    res = requests.post(f"{BASE_URL}/api/vehicle/service",
                        json={'vin': VIN, 'service_type': 'Fake Service'},
                        cookies=cookies, headers=HEADERS)
    
    if res.status_code == 400 or res.status_code == 401 or res.status_code == 500:
        log("System correctly rejected unauthorized user", "PASS")
    else:
        log(f"FAILED: Buyer was allowed to add service! Code: {res.status_code}", "FAIL")

if __name__ == "__main__":
    print("Ensure server is running on port 5001 before starting...")
    time.sleep(1)
    
    run_test("Full Vehicle Lifecycle", test_full_lifecycle)
    run_test("Security & Logic Checks", test_security_checks)

input("Press Enter to close...")