import requests
import base64
import json
import os
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
GENERATE_ENDPOINT = f"{BASE_URL}/generate"

DISCUSSIONS_DIR = Path(__file__).parent.absolute()
AUDIO_INPUT_FILE = DISCUSSIONS_DIR / "synthesis.wav"
VOICE_CLONE_FILE = DISCUSSIONS_DIR / "clone.wav"


def read_audio_as_base64(file_path) -> str:
    with open(str(file_path), "rb") as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode("utf-8")


def save_audio_response(response: requests.Response, output_file) -> None:
    with open(str(output_file), "wb") as f:
        f.write(response.content)
    print(f"✓ Audio saved to {output_file}")


def test_tts(text: str = "Hello Good morning and a warm welcome", voice: str = "alloy"):
    print("\n" + "="*60)
    print("TEST 1: TTS (Text-to-Speech)")
    print("="*60)
    
    start_time = time.time()
    payload = {
        "messages": [
            {
                "role": "system",
                "voice": voice,
                "content": [
                    {"type": "text", "text": "You are a helpful audio assistant. Synthesize the text naturally."}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text}
                ]
            }
        ],
        "seed": 42
    }
    
    try:
        print(f"Sending TTS request with voice '{voice}'...")
        print(f"Text: {text}")
        
        response = requests.post(GENERATE_ENDPOINT, json=payload, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            if response.headers.get("content-type") == "audio/wav":
                output_file = DISCUSSIONS_DIR / "test_output_tts.wav"
                save_audio_response(response, output_file)
                print(f"✓ TTS Test PASSED - Audio generated successfully")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return True
            else:
                print(f"✗ TTS Test FAILED - Expected audio/wav, got {response.headers.get('content-type')}")
                print(f"Response: {response.json()}")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return False
        else:
            error_data = response.json()
            print(f"✗ TTS Test FAILED - Status {response.status_code}")
            print(f"Error: {error_data}")
            print(f"⏱ Time taken: {elapsed_time:.2f}s")
            return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"✗ TTS Test FAILED with exception: {str(e)}")
        print(f"⏱ Time taken: {elapsed_time:.2f}s")
        return False


def test_ttt(text: str = "Tell me a short joke about programming."):
    print("\n" + "="*60)
    print("TEST 2: TTT (Text-to-Text)")
    print("="*60)
    
    start_time = time.time()
    payload = {
        "messages": [
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": "You are a witty assistant. Respond with a short text response only."}
                ]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text}
                ]
            }
        ],
        "seed": 42
    }
    
    try:
        print(f"Sending TTT request...")
        print(f"Prompt: {text}")
        
        response = requests.post(GENERATE_ENDPOINT, json=payload, timeout=30)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                response_text = data["choices"][0]["message"]["content"]
                print(f"✓ TTT Test PASSED")
                print(f"Response: {response_text}")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return True
            else:
                print(f"✗ TTT Test FAILED - Unexpected response format")
                print(f"Response: {data}")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return False
        else:
            error_data = response.json()
            print(f"✗ TTT Test FAILED - Status {response.status_code}")
            print(f"Error: {error_data}")
            print(f"⏱ Time taken: {elapsed_time:.2f}s")
            return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"✗ TTT Test FAILED with exception: {str(e)}")
        print(f"⏱ Time taken: {elapsed_time:.2f}s")
        return False


def test_sts(voice: str = "ballad"):
    print("\n" + "="*60)
    print("TEST 3: STS (Speech-to-Speech)")
    print("="*60)
    
    if not AUDIO_INPUT_FILE.exists():
        print(f"✗ STS Test FAILED - Audio input file not found: {AUDIO_INPUT_FILE}")
        return False
    
    start_time = time.time()
    try:
        print(f"Reading audio input from {AUDIO_INPUT_FILE}...")
        speech_audio_b64 = read_audio_as_base64(AUDIO_INPUT_FILE)
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "voice": voice,
                    "content": [
                        {"type": "text", "text": "Transform the input speech with your natural voice tone and clarity."}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transform this speech audio."},
                        {
                            "type": "speech_audio",
                            "audio": {"data": speech_audio_b64, "format": "wav"}
                        }
                    ]
                }
            ],
            "seed": 42
        }
        
        print(f"Sending STS request with voice '{voice}'...")
        
        response = requests.post(GENERATE_ENDPOINT, json=payload, timeout=60)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            if response.headers.get("content-type") == "audio/wav":
                output_file = DISCUSSIONS_DIR / "test_output_sts.wav"
                save_audio_response(response, output_file)
                print(f"✓ STS Test PASSED - Speech transformed successfully")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return True
            else:
                print(f"✗ STS Test FAILED - Expected audio/wav, got {response.headers.get('content-type')}")
                print(f"Response: {response.json()}")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return False
        else:
            error_data = response.json()
            print(f"✗ STS Test FAILED - Status {response.status_code}")
            print(f"Error: {error_data}")
            print(f"⏱ Time taken: {elapsed_time:.2f}s")
            return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"✗ STS Test FAILED with exception: {str(e)}")
        print(f"⏱ Time taken: {elapsed_time:.2f}s")
        return False


def test_stt():
    print("\n" + "="*60)
    print("TEST 4: STT (Speech-to-Text)")
    print("="*60)
    
    if not AUDIO_INPUT_FILE.exists():
        print(f"✗ STT Test FAILED - Audio input file not found: {AUDIO_INPUT_FILE}")
        return False
    
    start_time = time.time()
    try:
        print(f"Reading audio input from {AUDIO_INPUT_FILE}...")
        speech_audio_b64 = read_audio_as_base64(AUDIO_INPUT_FILE)
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "Transcribe the speech audio accurately to text."}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transcribe this audio."},
                        {
                            "type": "speech_audio",
                            "audio": {"data": speech_audio_b64, "format": "wav"}
                        }
                    ]
                }
            ],
            "seed": 42
        }
        
        print(f"Sending STT request...")
        
        response = requests.post(GENERATE_ENDPOINT, json=payload, timeout=60)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                transcription = data["choices"][0]["message"]["content"]
                print(f"✓ STT Test PASSED")
                print(f"Transcription: {transcription}")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return True
            else:
                print(f"✗ STT Test FAILED - Unexpected response format")
                print(f"Response: {data}")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return False
        else:
            error_data = response.json()
            print(f"✗ STT Test FAILED - Status {response.status_code}")
            print(f"Error: {error_data}")
            print(f"⏱ Time taken: {elapsed_time:.2f}s")
            return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"✗ STT Test FAILED with exception: {str(e)}")
        print(f"⏱ Time taken: {elapsed_time:.2f}s")
        return False


def test_sts_with_voice_cloning():
    print("\n" + "="*60)
    print("TEST 5: STS (Speech-to-Speech) with Voice Cloning")
    print("="*60)
    
    if not AUDIO_INPUT_FILE.exists():
        print(f"✗ STS Voice Clone Test FAILED - Audio input file not found: {AUDIO_INPUT_FILE}")
        return False
    
    if not VOICE_CLONE_FILE.exists():
        print(f"✗ STS Voice Clone Test FAILED - Voice clone file not found: {VOICE_CLONE_FILE}")
        return False
    
    start_time = time.time()
    try:
        print(f"Using voice clone file: {VOICE_CLONE_FILE}")
        
        print(f"Reading speech input from {AUDIO_INPUT_FILE}...")
        speech_audio_b64 = read_audio_as_base64(AUDIO_INPUT_FILE)
        
        payload = {
            "messages": [
                {
                    "role": "system",
                    "voice": str(VOICE_CLONE_FILE),
                    "content": [
                        {"type": "text", "text": "Clone this voice and maintain the speaker's tone and characteristics."}
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transform this speech with the cloned voice."},
                        {
                            "type": "speech_audio",
                            "audio": {"data": speech_audio_b64, "format": "wav"}
                        }
                    ]
                }
            ],
            "seed": 42
        }
        
        print(f"Sending STS request with voice cloning...")
        
        response = requests.post(GENERATE_ENDPOINT, json=payload, timeout=60)
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            if response.headers.get("content-type") == "audio/wav":
                output_file = DISCUSSIONS_DIR / "test_output_sts_voice_clone.wav"
                save_audio_response(response, output_file)
                print(f"✓ STS Voice Clone Test PASSED - Speech transformed with cloned voice")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return True
            else:
                print(f"✗ STS Voice Clone Test FAILED - Expected audio/wav, got {response.headers.get('content-type')}")
                print(f"Response: {response.json()}")
                print(f"⏱ Time taken: {elapsed_time:.2f}s")
                return False
        else:
            error_data = response.json()
            print(f"✗ STS Voice Clone Test FAILED - Status {response.status_code}")
            print(f"Error: {error_data}")
            print(f"⏱ Time taken: {elapsed_time:.2f}s")
            return False
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"✗ STS Voice Clone Test FAILED with exception: {str(e)}")
        print(f"⏱ Time taken: {elapsed_time:.2f}s")
        return False


def run_all_tests():
    print("\n" + "🚀 "*20)
    print("STARTING AUDIO POLLINATIONS TEST SUITE")
    print("🚀 "*20)
    
    suite_start_time = time.time()
    
    results = {
        "TTS": test_tts(),
        "TTT": test_ttt(),
        "STS": test_sts(),
        "STT": test_stt(),
        "STS_Voice_Clone": test_sts_with_voice_cloning(),
    }
    
    total_suite_time = time.time() - suite_start_time
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    print(f"Total time: {total_suite_time:.2f}s")
    print("="*60 + "\n")
    
    return results


if __name__ == "__main__":
    # run_all_tests()
    # test_sts_with_voice_cloning()
    # test_tts()
    # test_stt()
    # test_ttt()
    test_sts()
