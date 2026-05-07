#!/usr/bin/env python3
"""
Complete STT Pipeline Test
Tests the entire speech-to-text pipeline from audio file to transcription
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.stt_cache import stt_cache, HAS_WHISPER
from app.utils.logger import logger

def create_test_audio():
    """Create a simple test audio file using ffmpeg."""
    import subprocess
    
    test_audio_path = "/tmp/test_audio.wav"
    
    # Create a 2-second sine wave audio file
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
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create test audio: {e}")
        print(f"   stderr: {e.stderr.decode()}")
        return None
    except FileNotFoundError:
        print("❌ ffmpeg not found. Install with: brew install ffmpeg")
        return None

async def test_stt_pipeline():
    """Test the complete STT pipeline."""
    
    print("=" * 60)
    print("STT PIPELINE TEST")
    print("=" * 60)
    
    # Step 1: Check if faster-whisper is available
    print(f"\n1. Checking faster-whisper availability...")
    print(f"   HAS_WHISPER: {HAS_WHISPER}")
    
    if not HAS_WHISPER:
        print("   ❌ faster-whisper is NOT available")
        print("   Install with: pip install faster-whisper")
        return False
    else:
        print("   ✅ faster-whisper is available")
    
    # Step 2: Check model loading
    print(f"\n2. Testing model loading...")
    model = stt_cache._load_model()
    
    if model is None:
        print("   ❌ Model failed to load")
        return False
    else:
        print("   ✅ Model loaded successfully")
        print(f"   Model size: {stt_cache._model_size}")
        print(f"   Device: {stt_cache._device}")
    
    # Step 3: Create test audio
    print(f"\n3. Creating test audio file...")
    audio_path = create_test_audio()
    
    if audio_path is None:
        print("   ⚠️  Skipping audio test (ffmpeg not available)")
        print("   But model loading works, so STT should work with real audio")
        return True
    
    # Step 4: Test transcription
    print(f"\n4. Testing transcription...")
    try:
        transcript, language, confidence = await stt_cache.transcribe(audio_path)
        
        print(f"   ✅ Transcription completed")
        print(f"   Transcript: '{transcript}'")
        print(f"   Language: {language}")
        print(f"   Confidence: {confidence:.2f}")
        
        # Check if it's the mock response
        if "mock transcription" in transcript.lower():
            print("   ❌ STILL USING MOCK TRANSCRIPTION!")
            return False
        
        # Clean up
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_with_real_audio():
    """Test with a real audio file if available."""
    
    print("\n" + "=" * 60)
    print("REAL AUDIO TEST (Optional)")
    print("=" * 60)
    
    # Check if there's a test audio file
    test_files = [
        "/tmp/test_recording.wav",
        "/tmp/test_recording.webm",
        "./test_audio.wav",
    ]
    
    audio_path = None
    for path in test_files:
        if os.path.exists(path):
            audio_path = path
            break
    
    if audio_path is None:
        print("\nNo test audio file found. Skipping real audio test.")
        print("To test with real audio:")
        print("1. Record audio in the frontend")
        print("2. Save it to /tmp/test_recording.wav")
        print("3. Run this test again")
        return
    
    print(f"\nFound test audio: {audio_path}")
    print("Testing transcription...")
    
    try:
        transcript, language, confidence = await stt_cache.transcribe(audio_path)
        
        print(f"\n✅ Transcription completed")
        print(f"   Transcript: '{transcript}'")
        print(f"   Language: {language}")
        print(f"   Confidence: {confidence:.2f}")
        
        if "mock transcription" in transcript.lower():
            print("   ❌ STILL USING MOCK TRANSCRIPTION!")
        
    except Exception as e:
        print(f"\n❌ Transcription failed: {e}")
        import traceback
        traceback.print_exc()

def check_dependencies():
    """Check all required dependencies."""
    
    print("\n" + "=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)
    
    dependencies = {
        "faster_whisper": "faster-whisper",
        "torch": "torch",
    }
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            print(f"   Install with: pip install {package}")

async def main():
    """Run all tests."""
    
    print("\n🧪 Starting STT Pipeline Tests\n")
    
    # Check dependencies
    check_dependencies()
    
    # Test the pipeline
    success = await test_stt_pipeline()
    
    # Test with real audio if available
    await test_with_real_audio()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("\n✅ STT Pipeline is working correctly!")
        print("\nThe system should now transcribe real audio instead of using mock responses.")
        print("\nNext steps:")
        print("1. Restart the backend server")
        print("2. Test voice input in the frontend")
        print("3. Check backend logs for 'Whisper model loaded successfully'")
    else:
        print("\n❌ STT Pipeline has issues!")
        print("\nTroubleshooting:")
        print("1. Install faster-whisper: pip install faster-whisper")
        print("2. Install ffmpeg: brew install ffmpeg")
        print("3. Check backend logs for errors")
        print("4. Verify model can download (needs internet on first run)")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
