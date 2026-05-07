#!/usr/bin/env python3
"""
Test the /api/transcribe endpoint directly
"""

import requests
import subprocess
import os

def create_test_audio():
    """Create a simple test audio file."""
    test_audio_path = "/tmp/test_transcribe.wav"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", "sine=frequency=1000:duration=2",
        "-ar", "16000",
        "-ac", "1",
        test_audio_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✅ Test audio created: {test_audio_path}")
        return test_audio_path
    except Exception as e:
        print(f"❌ Failed to create test audio: {e}")
        return None

def test_transcribe_endpoint():
    """Test the transcribe endpoint."""
    
    print("=" * 60)
    print("TRANSCRIBE ENDPOINT TEST")
    print("=" * 60)
    
    # Create test audio
    print("\n1. Creating test audio...")
    audio_path = create_test_audio()
    
    if audio_path is None:
        print("   ❌ Cannot create test audio")
        return False
    
    # Test the endpoint
    url = "http://localhost:8000/api/transcribe"
    
    print(f"\n2. Sending POST request to {url}...")
    
    try:
        with open(audio_path, 'rb') as f:
            files = {'file': ('test.wav', f, 'audio/wav')}
            response = requests.post(url, files=files, timeout=30)
        
        print(f"\n3. Response received:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n4. Response data:")
            print(f"   transcript: '{data.get('transcript')}'")
            print(f"   detected_language: {data.get('detected_language')}")
            print(f"   language_probability: {data.get('language_probability')}")
            
            # Check if it's the mock response
            transcript = data.get('transcript', '')
            if "mock transcription" in transcript.lower():
                print(f"\n❌ STILL USING MOCK TRANSCRIPTION!")
                print(f"\nThis means:")
                print(f"1. The model is not loading when the endpoint is called")
                print(f"2. Check backend logs for errors")
                print(f"3. Verify faster-whisper is installed in the running environment")
                return False
            else:
                print(f"\n✅ Real transcription working!")
                return True
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {url}")
        print(f"   Make sure the backend server is running:")
        print(f"   cd backend && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if os.path.exists(audio_path):
            os.unlink(audio_path)

if __name__ == "__main__":
    print("\n🧪 Testing Transcribe Endpoint\n")
    success = test_transcribe_endpoint()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Transcription endpoint is working!")
    else:
        print("❌ Transcription endpoint has issues!")
        print("\nTroubleshooting:")
        print("1. Check if backend is running: curl http://localhost:8000/health")
        print("2. Check backend logs for 'Whisper model loaded successfully'")
        print("3. Verify faster-whisper is installed: pip list | grep faster-whisper")
        print("4. Check if model files downloaded: ls ~/.cache/huggingface/hub/")
    print("=" * 60)
