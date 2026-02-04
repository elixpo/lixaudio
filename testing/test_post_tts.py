import os
import sys
import requests


URL = "http://localhost:8000/generate"
out_audio_path = "generated.wav"

payload = {
    "messages": [
        {
            "role": "system",
            "voice": "alloy",
            "content": [{"type": "text", "text": "You are a helpful assistant that produces short speech."}]
        },
        {
            "role": "user",
            "content": [{"type": "text", "text": "Heeyyy buddy!! wassup haa? Tell me a joke!"}]
        }
    ],
    "seed": 42
}

def main():
    try:
        resp = requests.post(URL, json=payload, headers={"Content-Type": "application/json"}, stream=True, timeout=120)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not resp.ok:
        try:
            print("Server error:", resp.json(), file=sys.stderr)
        except Exception:
            print(f"Server returned status {resp.status_code}", file=sys.stderr)
        sys.exit(1)

    ctype = resp.headers.get("Content-Type", "")
    if "audio" in ctype:
        # save streamed audio to file
        with open(out_audio_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Saved audio to {out_audio_path}")

if __name__ == "__main__":
    main()