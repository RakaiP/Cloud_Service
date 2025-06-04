"""
Sync Service Testing - Python Script for Windows Compatibility
Tests the sync service endpoints without Windows curl issues
"""

import requests
import json
import time
from datetime import datetime

# Configuration
SYNC_SERVICE_URL = "http://localhost:8001"
METADATA_SERVICE_URL = "http://localhost:8000"
BLOCK_STORAGE_URL = "http://localhost:8003"

# Read token from .env file
def get_auth_token():
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('AUTH0_TOKEN='):
                    return line.split('=', 1)[1].strip()
    except FileNotFoundError:
        print("❌ .env file not found")
    return None

def test_sync_service():
    print("=" * 60)
    print("SYNC SERVICE COMPREHENSIVE TEST - PYTHON")
    print("=" * 60)
    
    # Get token
    token = get_auth_token()
    if token:
        headers_auth = {"Authorization": f"Bearer {token}"}
        print(f"✅ Token loaded: {token[:50]}...")
    else:
        headers_auth = {}
        print("❌ No token found in .env file")
    
    headers_json = {"Content-Type": "application/json"}
    headers_both = {**headers_json, **headers_auth}
    
    print(f"\nTesting sync service at: {SYNC_SERVICE_URL}")
    print("-" * 40)
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{SYNC_SERVICE_URL}/")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")
        if response.status_code == 200:
            print("   ✅ Root endpoint working")
        else:
            print("   ❌ Root endpoint failed")
    except requests.exceptions.ConnectionError:
        print("   ❌ Cannot connect to sync service")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{SYNC_SERVICE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health endpoint working")
        else:
            print("   ℹ️  Health endpoint not implemented (expected)")
    except Exception as e:
        print(f"   ℹ️  Health endpoint not found: {e}")
    
    # Test 3: Sync events creation (known working from tests)
    print("\n3. Testing sync event creation...")
    sync_event_data = {
        "event_type": "file_upload",
        "data": {
            "file_id": "python-test-123",
            "filename": "python-test.txt",
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(
            f"{SYNC_SERVICE_URL}/sync-events",
            headers=headers_json,
            json=sync_event_data
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        if response.status_code in [200, 201]:
            print("   ✅ Sync event creation working")
        else:
            print("   ❌ Sync event creation failed")
    except Exception as e:
        print(f"   ❌ Error creating sync event: {e}")
    
    # Test 4: Sync events with authentication
    print("\n4. Testing authenticated sync event...")
    if token:
        auth_event_data = {
            "event_type": "file_created",
            "file_id": "auth-test-456",
            "filename": "authenticated-test.txt",
            "device_id": "python-device-001"
        }
        
        try:
            response = requests.post(
                f"{SYNC_SERVICE_URL}/sync-events",
                headers=headers_both,
                json=auth_event_data
            )
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            if response.status_code in [200, 201]:
                print("   ✅ Authenticated sync event working")
            else:
                print("   ❌ Authenticated sync event failed")
        except Exception as e:
            print(f"   ❌ Error with authenticated event: {e}")
    else:
        print("   ⏭️  Skipping (no token)")
    
    # Test 5: List sync events
    print("\n5. Testing sync events list...")
    try:
        response = requests.get(f"{SYNC_SERVICE_URL}/sync-events")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Sync events list working")
            print(f"   Response: {response.text[:200]}")
        elif response.status_code == 404:
            print("   ℹ️  Sync events list endpoint not implemented")
        else:
            print(f"   ❌ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error listing sync events: {e}")
    
    # Test 6: Device management endpoints
    print("\n6. Testing device management...")
    device_data = {
        "device_id": "python-laptop-001",
        "device_name": "Python Test Laptop",
        "device_type": "desktop",
        "user_id": "python-test-user"
    }
    
    try:
        response = requests.post(
            f"{SYNC_SERVICE_URL}/devices",
            headers=headers_json,
            json=device_data
        )
        print(f"   Device registration status: {response.status_code}")
        if response.status_code in [200, 201]:
            print("   ✅ Device registration working")
        elif response.status_code == 404:
            print("   ℹ️  Device endpoint not implemented yet")
        else:
            print(f"   ❌ Device registration failed: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ Device registration error: {e}")
    
    # Test 7: Integration with other services
    print("\n7. Testing integration with other services...")
    
    # Check if metadata service is running
    try:
        response = requests.get(f"{METADATA_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Metadata service available")
            
            # Test integration flow
            print("   Testing integration flow...")
            if token:
                # Create file in metadata service
                file_data = {"filename": "sync-integration-test.txt"}
                try:
                    response = requests.post(
                        f"{METADATA_SERVICE_URL}/files",
                        headers=headers_both,
                        json=file_data
                    )
                    if response.status_code in [200, 201]:
                        print("   ✅ File created in metadata service")
                        file_response = response.json()
                        
                        # Notify sync service
                        sync_data = {
                            "event_type": "file_created",
                            "file_id": file_response.get("file_id", "integration-test"),
                            "filename": "sync-integration-test.txt",
                            "user_id": "python-test-user"
                        }
                        
                        response = requests.post(
                            f"{SYNC_SERVICE_URL}/sync-events",
                            headers=headers_json,
                            json=sync_data
                        )
                        if response.status_code in [200, 201]:
                            print("   ✅ Sync notification successful")
                        else:
                            print(f"   ❌ Sync notification failed: {response.status_code}")
                    else:
                        print(f"   ❌ File creation failed: {response.status_code}")
                except Exception as e:
                    print(f"   ❌ Integration test error: {e}")
            else:
                print("   ⏭️  Skipping integration test (no token)")
        else:
            print("   ❌ Metadata service not available")
    except Exception as e:
        print(f"   ❌ Cannot connect to metadata service: {e}")
    
    # Check block storage
    try:
        response = requests.get(f"{BLOCK_STORAGE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Block storage service available")
        else:
            print("   ❌ Block storage service not responding")
    except Exception as e:
        print(f"   ❌ Cannot connect to block storage: {e}")
    
    return True

def print_summary():
    print("\n" + "=" * 60)
    print("SYNC SERVICE TEST SUMMARY")
    print("=" * 60)
    print("\nBased on previous docker test results:")
    print("✅ Sync service foundation working (tests passing)")
    print("✅ PostgreSQL integration established")
    print("✅ Basic sync event creation functional")
    print("✅ Service running on Port 8001")
    
    print("\nNext steps for sync service enhancement:")
    print("1. Implement device management endpoints")
    print("2. Add real-time sync notifications (WebSocket)")
    print("3. Create sync queue per device")
    print("4. Add conflict resolution mechanisms")
    print("5. Enhance integration with metadata service")
    
    print("\nTo enhance sync service, run:")
    print("  enhance-sync-service.bat")
    print("  sync-service-integration-test.bat")

if __name__ == "__main__":
    success = test_sync_service()
    print_summary()
    
    if success:
        print("\n🎉 Sync service testing completed!")
    else:
        print("\n❌ Sync service testing failed!")
