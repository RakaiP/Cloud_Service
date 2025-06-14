import requests
import json
import time

def get_auth0_token():
    """Get Auth0 token"""
    url = "https://dev-mc721bw3z72t3xex.us.auth0.com/oauth/token"
    headers = {"content-type": "application/json"}
    data = {
        "client_id": "LbzsusVrT7HqFFWf3hkmrRMKKdRqEojc",
        "client_secret": "mDNn0upQAdNPjQaBwb5UGc-c_4hDr3f5PP8xhawlB8APYGFTw0fYhWxJPSNoGiq5",
        "audience": "https://cloud-api.rakai/",
        "grant_type": "client_credentials"
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        token_data = response.json()
        return token_data.get("access_token")
    return None

def test_sync_with_real_upload():
    """Test sync with an actual file upload"""
    print("🔄 Testing Sync with Real File Upload")
    print("=" * 50)
    
    token = get_auth0_token()
    if not token:
        print("❌ Could not get Auth0 token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Upload a real file to trigger sync
    print("\n1. 📁 Uploading file to chunker service...")
    try:
        # Create a test file
        test_content = f"Test file for sync - {time.time()}"
        
        with open("sync_test_file.txt", "w") as f:
            f.write(test_content)
        
        with open("sync_test_file.txt", "rb") as f:
            files = {"file": ("sync_test_file.txt", f, "text/plain")}
            response = requests.post(
                "http://localhost:8002/upload",
                files=files,
                headers=headers,
                timeout=30
            )
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✅ File uploaded: {upload_result}")
            file_id = upload_result.get("file_id")
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return
    
    # 2. Wait for automatic sync processing
    print("\n2. ⏳ Waiting for automatic sync processing...")
    time.sleep(8)  # Give more time for processing
    
    # 3. Check sync events for this file
    print(f"\n3. 🔍 Checking sync events for file {file_id[:20]}...")
    try:
        response = requests.get(
            f"http://localhost:8001/sync-events/{file_id}/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            sync_status = response.json()
            print(f"✅ File Sync Status:")
            for key, value in sync_status.items():
                print(f"   {key}: {value}")
                
            # Check if sync completed successfully
            if sync_status.get("sync_status") == "completed":
                print("\n🎉 SYNC SUCCESS: File uploaded and synchronized!")
            elif sync_status.get("sync_status") == "pending":
                print("\n⏳ SYNC PENDING: File sync still processing")
            else:
                print(f"\n⚠️ SYNC STATUS: {sync_status.get('sync_status')}")
                
        else:
            print(f"❌ Could not get sync status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Sync status error: {e}")
    
    # 4. List all recent sync events
    print("\n4. 📋 Recent sync events:")
    try:
        response = requests.get(
            "http://localhost:8001/sync-events?limit=5",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            events = response.json()
            print(f"Found {len(events)} recent events:")
            for i, event in enumerate(events):
                status_icon = "✅" if event["status"] == "completed" else "⏳" if event["status"] == "processing" else "❌"
                print(f"   {i+1}. {status_icon} {event['event_type']} - {event['status']} - {event['file_id'][:20]}...")
        else:
            print(f"❌ Could not get events: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Events error: {e}")
    
    # Cleanup
    try:
        import os
        os.remove("sync_test_file.txt")
    except:
        pass
    
    print("\n" + "=" * 50)
    print("🎯 Sync Integration Test Complete!")

if __name__ == "__main__":
    test_sync_with_real_upload()
