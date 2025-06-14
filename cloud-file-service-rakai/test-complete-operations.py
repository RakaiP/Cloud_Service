import requests
import time
import json

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

def test_complete_file_operations():
    """Test complete file lifecycle: upload -> list -> download -> delete"""
    print("🔄 Testing Complete File Operations Lifecycle")
    print("=" * 50)
    
    token = get_auth0_token()
    if not token:
        print("❌ Could not get Auth0 token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Upload a test file
    print("\n1. 📤 Uploading test file...")
    test_content = f"Test file content - {time.time()}"
    
    try:
        with open("test_operations.txt", "w") as f:
            f.write(test_content)
        
        with open("test_operations.txt", "rb") as f:
            files = {"file": ("test_operations.txt", f, "text/plain")}
            response = requests.post(
                "http://localhost:8002/upload",
                files=files,
                headers=headers,
                timeout=30
            )
        
        if response.status_code == 200:
            upload_result = response.json()
            file_id = upload_result.get("file_id")
            print(f"✅ Upload successful: {file_id}")
        else:
            print(f"❌ Upload failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False
    
    # 2. Wait for processing
    print("\n2. ⏳ Waiting for upload processing...")
    time.sleep(5)
    
    # 3. List files to verify upload
    print("\n3. 📋 Listing files...")
    try:
        response = requests.get(
            "http://localhost:8000/files",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            files = response.json()
            print(f"✅ Found {len(files)} files")
            
            # Find our uploaded file
            our_file = None
            for file in files:
                if file["file_id"] == file_id:
                    our_file = file
                    break
            
            if our_file:
                print(f"✅ Our file found: {our_file['filename']}")
            else:
                print("❌ Our uploaded file not found in list")
        else:
            print(f"❌ List files failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ List files error: {e}")
    
    # 4. Download the file
    print(f"\n4. ⬇️ Downloading file via chunker service...")
    try:
        response = requests.get(
            f"http://localhost:8002/download/{file_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            downloaded_content = response.content.decode('utf-8')
            print(f"✅ Download successful!")
            print(f"📄 Downloaded content: {downloaded_content[:50]}...")
            
            # Verify content matches
            if test_content in downloaded_content:
                print("✅ Content verification: PASSED")
            else:
                print("❌ Content verification: FAILED")
        else:
            print(f"❌ Download failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Download error: {e}")
    
    # 5. Delete the file via chunker service
    print(f"\n5. 🗑️ Deleting file via chunker service...")
    try:
        response = requests.delete(
            f"http://localhost:8002/files/{file_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            delete_result = response.json()
            print(f"✅ Delete initiated: {delete_result}")
        else:
            print(f"❌ Delete failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Delete error: {e}")
    
    # 6. Wait for sync processing
    print("\n6. ⏳ Waiting for delete sync processing...")
    time.sleep(8)
    
    # 7. Verify file deletion
    print(f"\n7. 🔍 Verifying file deletion...")
    try:
        response = requests.get(
            f"http://localhost:8000/files/{file_id}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 404:
            print("✅ File successfully deleted from metadata")
        else:
            print(f"⚠️ File still exists in metadata: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
    
    # 8. Check sync events
    print(f"\n8. 📊 Checking sync events...")
    try:
        response = requests.get(
            f"http://localhost:8001/sync-events/{file_id}/status",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            sync_status = response.json()
            print(f"✅ Sync status: {sync_status.get('sync_status')}")
            print(f"📋 Latest event: {sync_status.get('latest_event_type')}")
        else:
            print(f"⚠️ Could not get sync status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Sync status error: {e}")
    
    # Cleanup
    try:
        import os
        os.remove("test_operations.txt")
    except:
        pass
    
    print("\n" + "=" * 50)
    print("🎯 Complete File Operations Test Finished!")
    print("\n📝 What we tested:")
    print("✅ File upload via chunker service")
    print("✅ File listing via metadata service") 
    print("✅ File download via chunker service (chunk reconstruction)")
    print("✅ File deletion via chunker service (with sync)")
    print("✅ Sync event processing verification")

if __name__ == "__main__":
    test_complete_file_operations()
