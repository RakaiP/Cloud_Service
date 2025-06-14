import requests
import time

def test_cors_and_connectivity():
    """Test CORS and service connectivity"""
    print("🔧 Testing CORS and Service Connectivity")
    print("=" * 60)
    
    services = [
        ("Metadata Service", "http://localhost:8000/health"),
        ("Sync Service", "http://localhost:8001/health"),
        ("Chunker Service", "http://localhost:8002/health"),
        ("Block Storage", "http://localhost:8003/health"),
    ]
    
    for service_name, url in services:
        print(f"\n🔍 Testing {service_name}")
        print("-" * 40)
        
        # Test OPTIONS request (preflight)
        try:
            options_response = requests.options(url, timeout=5)
            print(f"   ✅ OPTIONS /health: {options_response.status_code}")
            
            # Check CORS headers in OPTIONS response
            cors_headers = options_response.headers.get('Access-Control-Allow-Methods')
            if cors_headers:
                print(f"   ✅ CORS Methods: {cors_headers}")
            else:
                print("   ⚠️  Missing CORS Methods header")
                
        except requests.exceptions.ConnectTimeout:
            print("   ❌ OPTIONS timeout - service may be down")
        except requests.exceptions.ConnectionError as e:
            if "RemoteDisconnected" in str(e) or "ConnectionAbortedError" in str(e):
                print("   ❌ Service crashed during OPTIONS request")
            else:
                print(f"   ❌ OPTIONS connection failed: {e}")
        except Exception as e:
            print(f"   ❌ OPTIONS failed: {e}")
        
        # Test GET request (actual request)
        try:
            get_response = requests.get(url, timeout=5)
            print(f"   ✅ GET /health: {get_response.status_code}")
            
            if get_response.status_code == 200:
                try:
                    data = get_response.json()
                    print(f"   📊 Service Status: {data.get('status', 'unknown')}")
                except:
                    print("   📊 Service responding (non-JSON)")
                    
                # Check CORS headers in GET response
                origin = get_response.headers.get('Access-Control-Allow-Origin')
                if origin:
                    print(f"   ✅ CORS Origin: {origin}")
                else:
                    print("   ⚠️  Missing CORS Origin header")
            else:
                print(f"   ⚠️  Unexpected status code: {get_response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print("   ❌ GET timeout - service may be overloaded")
        except requests.exceptions.ConnectionError as e:
            if "RemoteDisconnected" in str(e) or "ConnectionAbortedError" in str(e):
                print("   ❌ Service crashed during GET request")
            else:
                print(f"   ❌ GET connection failed: connection refused")
        except Exception as e:
            print(f"   ❌ GET failed: {e}")

def test_service_recovery():
    """Test if services recover after restart"""
    print("\n🔄 Testing Service Recovery")
    print("=" * 40)
    
    print("Waiting 10 seconds for services to stabilize...")
    time.sleep(10)
    
    services = [
        ("Metadata", "http://localhost:8000/health"),
        ("Sync", "http://localhost:8001/health"),
        ("Chunker", "http://localhost:8002/health"),
        ("Block Storage", "http://localhost:8003/health"),
    ]
    
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"   ✅ {service_name}: Recovered")
            else:
                print(f"   ⚠️  {service_name}: Status {response.status_code}")
        except Exception:
            print(f"   ❌ {service_name}: Still down")

if __name__ == "__main__":
    print("🚀 CORS and Connectivity Test")
    print("This will test if all services handle CORS properly and are responsive")
    
    test_cors_and_connectivity()
    test_service_recovery()
    
    print("\n" + "=" * 60)
    print("🎯 Summary:")
    print("- If sync service shows crash errors, restart it: docker compose restart sync-service")
    print("- If block storage shows 405 errors, the CORS fix needs to be applied")
    print("- All services should respond to both OPTIONS and GET requests")
    print("\n💡 To fix issues:")
    print("1. docker compose restart")
    print("2. docker compose logs sync-service (check for errors)")
    print("3. Re-run this test")
if __name__ == "__main__":
    print("🚀 Starting Comprehensive CORS and Connectivity Test")
    
    # Test CORS fixes
    cors_ok = test_cors_fix_all_services()
    
    # Test connectivity
    test_service_connectivity()
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATIONS:")
    
    if cors_ok:
        print("✅ CORS is working correctly")
        print("✅ Your frontend should now connect successfully")
        print("🔄 Try refreshing your browser and test file upload")
    else:
        print("🔧 To fix remaining issues:")
        print("1. docker compose restart")
        print("2. Wait 30 seconds for services to start")
        print("3. Run this test again")
        print("4. Check docker compose logs for any errors")
    
    print("\n🌐 Frontend Testing:")
    print("1. Open http://localhost:80")
    print("2. Use 'Use API Token' option")
    print("3. All 4 services should show ✅ Healthy")
    print("4. File upload should work end-to-end")
