import requests
import json

def test_services_direct():
    """Test services directly without nginx proxy"""
    print("=== Testing Services Directly ===")
    
    services = [
        ("Metadata Service", "http://localhost:8000/health"),
        ("Block Storage", "http://localhost:8003/health"),
        ("Chunker Service", "http://localhost:8002/health"),
        ("Sync Service", "http://localhost:8001/health"),
    ]
    
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=10)
            print(f"\n{service_name}:")
            print(f"  Status Code: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('content-type', 'Unknown')}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"  Response: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"  Raw Response: {response.text[:200]}...")
            else:
                print(f"  Error Response: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"\n{service_name}: ❌ Connection refused - service not running")
        except requests.exceptions.Timeout:
            print(f"\n{service_name}: ❌ Timeout - service not responding")
        except Exception as e:
            print(f"\n{service_name}: ❌ Error: {e}")

def test_frontend_access():
    """Test if frontend is accessible"""
    print("\n=== Testing Frontend Access ===")
    try:
        response = requests.get("http://localhost:80", timeout=5)
        print(f"Frontend Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
        if response.status_code == 200:
            print("✅ Frontend is accessible")
        else:
            print(f"❌ Frontend error: {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")

if __name__ == "__main__":
    test_services_direct()
    test_frontend_access()
    
    print("\n=== Instructions ===")
    print("1. If services work directly, the nginx proxy configuration needs fixing")
    print("2. If services don't work directly, check docker compose logs")
    print("3. Run: docker compose ps to see which services are running")
    print("4. Run: docker compose logs <service-name> to check specific service logs")
