import requests
import json
import os

BASE_URL = "http://localhost:8003"

def test_health():
    print("1. Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}\n")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}\n")
        return False

def test_stats():
    print("2. Testing Stats...")
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_list_chunks():
    print("3. Testing List Chunks...")
    response = requests.get(f"{BASE_URL}/chunks")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_upload_chunk():
    print("4. Testing Upload Chunk...")
    
    # Create test file
    test_content = "This is a test chunk for Python testing"
    with open("test-chunk.txt", "w") as f:
        f.write(test_content)
    
    print(f"Created test file with content: '{test_content}'")
    
    # Upload chunk
    try:
        with open("test-chunk.txt", "rb") as f:
            files = {"file": f}
            data = {"chunk_id": "python-test-chunk"}
            print("Sending POST request...")
            response = requests.post(f"{BASE_URL}/chunks", files=files, data=data)
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error Response: {response.text}")
        print()
        return response.status_code == 200
    except Exception as e:
        print(f"Upload failed with exception: {e}\n")
        return False

def test_download_chunk():
    print("5. Testing Download Chunk...")
    response = requests.get(f"{BASE_URL}/chunks/python-test-chunk")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        with open("downloaded-chunk.txt", "wb") as f:
            f.write(response.content)
        print("Chunk downloaded successfully")
        with open("downloaded-chunk.txt", "r") as f:
            print(f"Content: {f.read()}\n")

def test_delete_chunk():
    print("6. Testing Delete Chunk...")
    response = requests.delete(f"{BASE_URL}/chunks/python-test-chunk")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def cleanup():
    for file in ["test-chunk.txt", "downloaded-chunk.txt"]:
        if os.path.exists(file):
            os.remove(file)

if __name__ == "__main__":
    print("===== TESTING BLOCK STORAGE ENDPOINTS =====\n")
    
    try:
        # First check if service is healthy
        if not test_health():
            print("Service health check failed. Check if services are running.")
            exit(1)
            
        test_stats()
        test_list_chunks()
        
        # Try upload
        if test_upload_chunk():
            test_list_chunks()  # Should show uploaded chunk
            test_download_chunk()
            test_delete_chunk()
            test_list_chunks()  # Should be empty again
        else:
            print("Upload failed, skipping remaining tests")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to block-storage service. Make sure it's running on port 8003.")
        print("Run: docker-compose ps to check service status")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        cleanup()
    
    print("===== TESTING COMPLETE =====")
