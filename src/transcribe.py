from model_client import model_client
from loguru import logger
import asyncio

async def transcribe_audio_from_base64(synthesis_audio_path: str, reqID: str, model_size: str = "small") -> str:
    logger.info(f"Transcribing audio from base64 file: {synthesis_audio_path} for request ID: {reqID} using model size: {model_size}")
    
    with open(synthesis_audio_path, "r") as f:
        b64_audio = f.read().strip()
    
    # Use model client instead of direct model access
    result = await model_client.transcribe_audio(b64_audio, reqID, model_size)
    return result

if __name__ == "__main__":
    async def main():
        reqID = "test_request"
        synthesis_audio_path = "/tmp/higgs/test_request/voice_test_request.txt"
        text = await transcribe_audio_from_base64(synthesis_audio_path, reqID, model_size="small")
        print("\n--- Transcription ---\n")
        print(text)
    asyncio.run(main())