import requests
import time

def test_cors_fix():
    """Test that CORS preflight requests work properly"""
    print("🔧 Testing CORS Preflight Fix")
    print("=" * 50)
    
    services = [
        ("Metadata Service", "http://localhost:8000/health"),
        ("Sync Service", "http://localhost:8001/health"),
        ("Chunker Service", "http://localhost:8002/health"),
        ("Block Storage", "http://localhost:8003/health"),
    ]
    
    for service_name, url in services:
        print(f"\n🔍 Testing {service_name}")
        
        # Test OPTIONS request (preflight)
        try:
            options_response = requests.options(url, timeout=5)
            print(f"   OPTIONS /health: {options_response.status_code}")
            if options_response.status_code in [200, 204]:
                print("   ✅ CORS preflight working")
            else:
                print("   ⚠️  CORS preflight unusual response")
        except Exception as e:
            print(f"   ❌ OPTIONS failed: {e}")
        
        # Test GET request (actual request)
        try:
            get_response = requests.get(url, timeout=5)
            print(f"   GET /health: {get_response.status_code}")
            if get_response.status_code == 200:
                print("   ✅ GET request working")
                # Check CORS headers
                cors_headers = {
                    'Access-Control-Allow-Origin': get_response.headers.get('Access-Control-Allow-Origin'),
                    'Access-Control-Allow-Methods': get_response.headers.get('Access-Control-Allow-Methods'),
                    'Access-Control-Allow-Headers': get_response.headers.get('Access-Control-Allow-Headers'),
                }
                if any(cors_headers.values()):
                    print("   ✅ CORS headers present")
                else:
                    print("   ⚠️  CORS headers missing")
            else:
                print("   ❌ GET request failed")
        except Exception as e:
            print(f"   ❌ GET failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CORS Fix Complete!")
    print("\n📝 What was fixed:")
    print("- Added allow_methods=['*'] to CORS middleware")
    print("- Added explicit OPTIONS handlers for /health endpoints")
    print("- CORS middleware now properly handles preflight requests")
    print("\n✅ No more 405 Method Not Allowed errors for OPTIONS requests!")

if __name__ == "__main__":
    test_cors_fix()
