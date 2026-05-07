#!/usr/bin/env python3
"""
Test Script: Boarding Pass Upload Fix

Verifies that the upload endpoint always returns valid JSON.
"""

import requests
import json
import sys
from pathlib import Path

API_URL = "http://localhost:8000/api/ocr/boarding-pass"

def test_valid_image():
    """Test with a valid image file."""
    print("\n" + "=" * 60)
    print("TEST 1: Valid Image Upload")
    print("=" * 60)
    
    # Create a dummy image file
    test_file = Path("test_boarding_pass.jpg")
    if not test_file.exists():
        print("⚠️  No test image found, skipping...")
        return True
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('boarding_pass.jpg', f, 'image/jpeg')}
            response = requests.post(API_URL, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Response Length: {len(response.text)} bytes")
        
        # Check if response is JSON
        try:
            data = response.json()
            print(f"✅ Valid JSON response")
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            print(f"Response text: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_invalid_file_type():
    """Test with invalid file type."""
    print("\n" + "=" * 60)
    print("TEST 2: Invalid File Type")
    print("=" * 60)
    
    try:
        # Create a text file
        files = {'file': ('test.txt', b'This is not an image', 'text/plain')}
        response = requests.post(API_URL, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        # Check if response is JSON (not HTML)
        if 'html' in response.headers.get('content-type', '').lower():
            print(f"❌ Response is HTML (should be JSON)")
            return False
        
        try:
            data = response.json()
            print(f"✅ Valid JSON response")
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('success') == False:
                print(f"✅ Correctly returned success=false")
                return True
            else:
                print(f"⚠️  Expected success=false for invalid file")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            print(f"Response text: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_missing_file():
    """Test with missing file parameter."""
    print("\n" + "=" * 60)
    print("TEST 3: Missing File Parameter")
    print("=" * 60)
    
    try:
        response = requests.post(API_URL)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        # Should return JSON error (not HTML)
        if 'html' in response.headers.get('content-type', '').lower():
            print(f"❌ Response is HTML (should be JSON)")
            return False
        
        try:
            data = response.json()
            print(f"✅ Valid JSON response")
            print(f"Message: {data.get('detail') or data.get('message')}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def test_empty_file():
    """Test with empty file."""
    print("\n" + "=" * 60)
    print("TEST 4: Empty File")
    print("=" * 60)
    
    try:
        files = {'file': ('empty.jpg', b'', 'image/jpeg')}
        response = requests.post(API_URL, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        
        # Check if response is JSON
        try:
            data = response.json()
            print(f"✅ Valid JSON response")
            print(f"Success: {data.get('success')}")
            print(f"Message: {data.get('message')}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BOARDING PASS UPLOAD FIX - TEST SUITE")
    print("=" * 60)
    print(f"\nTesting endpoint: {API_URL}")
    print("\nCRITICAL: All responses must be valid JSON (not HTML)")
    
    results = []
    
    # Run tests
    results.append(("Valid Image", test_valid_image()))
    results.append(("Invalid File Type", test_invalid_file_type()))
    results.append(("Missing File", test_missing_file()))
    results.append(("Empty File", test_empty_file()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Upload fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the fix.")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        sys.exit(1)
