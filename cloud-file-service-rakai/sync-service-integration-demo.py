"""
Sync Service Integration Demo
Shows how sync service integrates with the complete file upload/download flow
"""

import requests
import json
import time
from datetime import datetime

# Service URLs
METADATA_SERVICE_URL = "http://localhost:8000"
BLOCK_STORAGE_URL = "http://localhost:8003"
SYNC_SERVICE_URL = "http://localhost:8001"

def get_auth_token():
    """Read token from .env file"""
    try:
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('AUTH0_TOKEN='):
                    return line.split('=', 1)[1].strip()
    except FileNotFoundError:
        print("❌ .env file not found")
    return None

def demonstrate_file_upload_sync_flow():
    """Demonstrate complete file upload with sync notifications"""
    print("🔄 COMPLETE FILE UPLOAD + SYNC FLOW DEMONSTRATION")
    print("=" * 60)
    
    token = get_auth_token()
    if not token:
        print("❌ No authentication token found")
        return False
    
    auth_headers = {"Authorization": f"Bearer {token}"}
    json_headers = {"Content-Type": "application/json"}
    both_headers = {**auth_headers, **json_headers}
    
    # Step 1: Create test file content
    print("\n1. Preparing test file...")
    test_filename = f"sync-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
    test_content = f"""Sync Integration Demo File
Created: {datetime.now().isoformat()}
Purpose: Demonstrate sync service integration with file operations
Content: This file tests the complete flow from upload to sync notification
"""
    
    print(f"   📄 File: {test_filename}")
    print(f"   📏 Size: {len(test_content)} bytes")
    
    # Step 2: Upload to Block Storage (direct)
    print("\n2. Uploading to Block Storage...")
    try:
        # Create chunk ID
        chunk_id = f"{test_filename}-chunk-001"
        
        # Upload to block storage
        files = {'file': (test_filename, test_content)}
        data = {'chunk_id': chunk_id}
        
        response = requests.post(
            f"{BLOCK_STORAGE_URL}/chunks",
            files=files,
            data=data
        )
        
        if response.status_code in [200, 201]:
            print(f"   ✅ Block storage upload successful")
            print(f"   📦 Chunk ID: {chunk_id}")
        else:
            print(f"   ❌ Block storage upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Block storage error: {e}")
        return False
    
    # Step 3: Create file metadata
    print("\n3. Creating file metadata...")
    try:
        metadata = {
            "filename": test_filename,
            "size": len(test_content)
        }
        
        response = requests.post(
            f"{METADATA_SERVICE_URL}/files",
            headers=both_headers,
            json=metadata
        )
        
        if response.status_code in [200, 201]:
            file_data = response.json()
            file_id = file_data.get('file_id')
            print(f"   ✅ Metadata created successfully")
            print(f"   🆔 File ID: {file_id}")
        else:
            print(f"   ❌ Metadata creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Metadata service error: {e}")
        return False
    
    # Step 4: Notify Sync Service (current capabilities)
    print("\n4. Notifying Sync Service...")
    try:
        # Use current working event type
        sync_event = {
            "event_type": "upload",  # Current supported type
            "file_id": file_id,
            "filename": test_filename,
            "user_id": "demo-user",
            "device_id": "demo-device"
        }
        
        response = requests.post(
            f"{SYNC_SERVICE_URL}/sync-events",
            headers=both_headers,
            json=sync_event
        )
        
        if response.status_code in [200, 201]:
            sync_data = response.json()
            print(f"   ✅ Sync event created successfully")
            print(f"   🔄 Event: {sync_data}")
        else:
            print(f"   ❌ Sync notification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Sync service error: {e}")
        return False
    
    # Step 5: Verify sync events
    print("\n5. Verifying sync events...")
    try:
        response = requests.get(
            f"{SYNC_SERVICE_URL}/sync-events",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            events = response.json()
            print(f"   ✅ Found {len(events)} sync events")
            
            # Find our event
            our_event = None
            for event in events:
                if isinstance(event, dict) and event.get('file_id') == file_id:
                    our_event = event
                    break
            
            if our_event:
                print(f"   🎯 Our event found: {our_event}")
            else:
                print(f"   ⚠️  Our event not found in list")
                
        else:
            print(f"   ❌ Failed to verify events: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Event verification error: {e}")
    
    return True

def demonstrate_enhanced_sync_flow():
    """Demonstrate what enhanced sync flow would look like"""
    print("\n🚀 ENHANCED SYNC FLOW (Future Implementation)")
    print("=" * 60)
    
    print("Step 1: File Upload")
    print("  📤 Client uploads file chunks to Block Storage")
    print("  📝 Metadata Service records file information")
    print("  🔔 Metadata Service automatically notifies Sync Service")
    
    print("\nStep 2: Enhanced Sync Event")
    print("  📊 Event includes: file_id, filename, size, hash, chunks")
    print("  🏷️  Event type: 'file_created' (more specific than 'upload')")
    print("  🆔 Device and user information included")
    print("  ⏰ Timestamp for ordering and conflict resolution")
    
    print("\nStep 3: Device Notification")
    print("  📱 Sync Service identifies other user devices")
    print("  🔄 Creates pending sync operations for each device")
    print("  ⚡ Real-time WebSocket notifications sent")
    print("  📊 Sync queue updated for each device")
    
    print("\nStep 4: Client Sync")
    print("  📲 Other devices receive sync notification")
    print("  📥 Devices download file metadata from Metadata Service")
    print("  🧩 Devices download chunks from Block Storage")
    print("  🔧 Devices reconstruct file locally")
    print("  ✅ Devices mark sync as completed")
    
    print("\nStep 5: Conflict Resolution")
    print("  🔍 Sync Service detects simultaneous modifications")
    print("  ⚖️  Conflict resolution strategy applied")
    print("  🤝 User prompted for conflict resolution if needed")
    print("  📝 Resolution recorded in sync history")

def demonstrate_current_vs_enhanced():
    """Compare current capabilities vs needed enhancements"""
    print("\n📊 CURRENT VS ENHANCED CAPABILITIES")
    print("=" * 60)
    
    print("📋 CURRENT SYNC SERVICE CAPABILITIES:")
    print("  ✅ Basic sync event creation")
    print("  ✅ Event types: 'upload', 'delete', 'update'")
    print("  ✅ Authentication with Auth0 JWT")
    print("  ✅ Database persistence")
    print("  ✅ Health monitoring")
    print("  ✅ RESTful API structure")
    
    print("\n🚀 NEEDED ENHANCEMENTS:")
    print("  ❌ Expanded event types ('file_created', 'file_modified', etc.)")
    print("  ❌ Device management (register, track, notify)")
    print("  ❌ Sync queue per device")
    print("  ❌ Real-time notifications (WebSocket)")
    print("  ❌ Conflict detection and resolution")
    print("  ❌ Integration webhooks from Metadata Service")
    print("  ❌ Batch sync operations")
    print("  ❌ Sync analytics and monitoring")
    
    print("\n🎯 PRIORITY ORDER:")
    print("  1. Expand event types (immediate)")
    print("  2. Add device management (high)")
    print("  3. Implement sync queues (high)")
    print("  4. Add real-time notifications (medium)")
    print("  5. Conflict resolution (medium)")
    print("  6. Advanced features (low)")

def main():
    """Main integration demonstration"""
    print("🔧 SYNC SERVICE INTEGRATION DEMONSTRATION")
    print("=" * 60)
    print("This demonstrates how sync service integrates with file operations")
    print()
    
    # Demonstrate current integration
    success = demonstrate_file_upload_sync_flow()
    
    if success:
        print("\n🎉 Current integration working!")
    else:
        print("\n❌ Integration issues detected")
    
    # Show enhanced flow
    demonstrate_enhanced_sync_flow()
    
    # Compare capabilities
    demonstrate_current_vs_enhanced()
    
    print("\n" + "=" * 60)
    print("🔄 SYNC SERVICE INTEGRATION SUMMARY:")
    print()
    print("✅ WORKING TODAY:")
    print("  - Basic sync event creation")
    print("  - Manual integration with metadata and block storage")
    print("  - Authentication and persistence")
    print()
    print("🚀 ENHANCEMENT OPPORTUNITIES:")
    print("  - Automatic webhook integration")
    print("  - Device-aware sync management")
    print("  - Real-time sync notifications")
    print("  - Conflict resolution mechanisms")
    print()
    print("🎯 NEXT STEPS:")
    print("  1. Run: python enhance-sync-service-phase1.py")
    print("  2. Implement enhanced event types in sync service")
    print("  3. Add device management endpoints")
    print("  4. Create metadata service webhook integration")
    print("  5. Implement real-time sync capabilities")

if __name__ == "__main__":
    main()
