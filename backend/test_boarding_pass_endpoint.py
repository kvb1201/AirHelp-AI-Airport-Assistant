#!/usr/bin/env python3
"""
Test script for boarding pass upload endpoint
Tests the complete pipeline from file upload to JSON response
"""

import requests
import io
from PIL import Image
import sys

def create_test_image():
    """Create a simple test image."""
    img = Image.new('RGB', (800, 400), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes

def test_boarding_pass_upload():
    """Test the boarding pass upload endpoint."""
    
    print("=" * 60)
    print("BOARDING PASS UPLOAD ENDPOINT TEST")
    print("=" * 60)
    
    # Create test image
    print("\n1. Creating test image...")
    test_image = create_test_image()
    print("   ✓ Test image created (800x400 JPEG)")
    
    # Prepare the request
    url = "http://localhost:8000/api/ocr/boarding-pass"
    files = {'file': ('test_boarding_pass.jpg', test_image, 'image/jpeg')}
    
    print(f"\n2. Sending POST request to {url}...")
    
    try:
        response = requests.post(url, files=files, timeout=10)
        
        print(f"\n3. Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"   Content-Length: {len(response.content)} bytes")
        
        # Check if response is empty
        if len(response.content) == 0:
            print("\n   ❌ ERROR: Response body is EMPTY!")
            print("   This is the root cause of 'Server returned empty response'")
            return False
        
        # Try to parse as JSON
        print(f"\n4. Parsing response...")
        try:
            data = response.json()
            print(f"   ✓ JSON parsed successfully")
            
            # Display the response structure
            print(f"\n5. Response structure:")
            print(f"   success: {data.get('success')}")
            print(f"   message: {data.get('message')}")
            print(f"   timestamp: {data.get('timestamp')}")
            print(f"   confidence: {data.get('confidence')}")
            
            if 'data' in data:
                print(f"\n6. Extracted data:")
                for key, value in data['data'].items():
                    print(f"   {key}: {value}")
            
            # Check if successful
            if data.get('success'):
                print(f"\n✅ TEST PASSED: Boarding pass extracted successfully")
                return True
            else:
                print(f"\n⚠️  TEST WARNING: Request succeeded but extraction failed")
                print(f"   Message: {data.get('message')}")
                return True  # Still a valid JSON response
                
        except ValueError as e:
            print(f"   ❌ ERROR: Failed to parse JSON")
            print(f"   Error: {e}")
            print(f"\n   Raw response (first 500 chars):")
            print(f"   {response.text[:500]}")
            
            # Check if it's HTML
            if response.text.startswith('<!DOCTYPE') or '<html' in response.text:
                print(f"\n   ❌ Server returned HTML instead of JSON!")
                print(f"   This indicates an unhandled exception in the backend")
            
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n   ❌ ERROR: Could not connect to {url}")
        print(f"   Make sure the backend server is running on port 8000")
        return False
        
    except requests.exceptions.Timeout:
        print(f"\n   ❌ ERROR: Request timed out after 10 seconds")
        return False
        
    except Exception as e:
        print(f"\n   ❌ ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_curl():
    """Print curl command for manual testing."""
    print("\n" + "=" * 60)
    print("MANUAL CURL TEST COMMAND")
    print("=" * 60)
    print("\nCreate a test image first:")
    print("  python3 -c \"from PIL import Image; img = Image.new('RGB', (800, 400), 'white'); img.save('test.jpg')\"")
    print("\nThen run this curl command:")
    print("  curl -X POST http://localhost:8000/api/ocr/boarding-pass \\")
    print("       -F 'file=@test.jpg' \\")
    print("       -v")
    print("\nLook for:")
    print("  - HTTP status code (should be 200)")
    print("  - Content-Type header (should be application/json)")
    print("  - Response body (should be valid JSON)")
    print("=" * 60)

if __name__ == "__main__":
    print("\n🧪 Starting Boarding Pass Upload Test\n")
    
    # Run the test
    success = test_boarding_pass_upload()
    
    # Print curl command for manual testing
    test_with_curl()
    
    # Exit with appropriate code
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        print("\nTroubleshooting steps:")
        print("1. Check if backend is running: curl http://localhost:8000/api/ocr/status")
        print("2. Check backend logs for errors")
        print("3. Verify FastAPI response_model is working correctly")
        print("4. Test with curl command above")
        sys.exit(1)
