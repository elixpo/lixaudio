from utility import encode_audio_base64, save_temp_audio, validate_and_decode_base64_audio, convertToAudio
from multiprocessing.managers import BaseManager
from voiceMap import VOICE_BASE64_MAP
from typing import Optional, Tuple
import asyncio
import torchaudio
import torch 
from intent import getContentRefined
import io


class ModelManager(BaseManager): pass
ModelManager.register("Service")
manager = ModelManager(address=("localhost", 6000), authkey=b"secret")
manager.connect()
service = manager.Service()

async def generate_sts(text: str, audio_base64_path: str, requestID: str, system: Optional[str] = None, voice: Optional[str] = "alloy") -> Tuple[bytes, int]:
    clone_path = None
    
    # Resolve voice path
    if voice and not VOICE_BASE64_MAP.get(voice):
        # Try to use as direct file path
        try:
            with open(voice, "r") as f:
                audio_data = f.read()
                if validate_and_decode_base64_audio(audio_data):
                    clone_path = voice
        except Exception as e:
            print(f"[{requestID}] Failed to load voice from path {voice}: {e}. Falling back to alloy.")
            clone_path = VOICE_BASE64_MAP.get("alloy")
    elif voice and VOICE_BASE64_MAP.get(voice):
        # Use named voice from map
        clone_path = VOICE_BASE64_MAP.get(voice)
    else:
        # Default to alloy
        clone_path = VOICE_BASE64_MAP.get("alloy")
    
    try:
        # Transcribe input audio
        print(f"[{requestID}] Transcribing input audio...")
        transcription = service.transcribe(audio_base64_path, requestID)
        print(f"[{requestID}] Transcription result: {transcription[:100]}...")
        
        # Detect intent and refine response
        print(f"[{requestID}] Detecting intent and refining content...")
        intention_detection = await getContentRefined(
            f"This is the prompt and {text} and this is the audio transcript {transcription}",
            system
        )
        
        intention = intention_detection.get("intent")
        content = intention_detection.get("content")
        refined_system = intention_detection.get("system_instruction")
        
        print(f"[{requestID}] Intent: {intention}, Generated content: {content[:100]}...")
        
        # Generate audio using ChatterboxTurboTTS
        print(f"[{requestID}] Generating STS audio with voice: {voice}")
        wav, sample_rate = service.speechSynthesis(chatTemplate=content, audio_prompt_path=clone_path)
        
        if wav is None:
            raise RuntimeError("Audio generation failed - GPU out of memory or other error")
        
        # Convert to WAV bytes
        if isinstance(wav, torch.Tensor):
            audio_tensor = wav.unsqueeze(0) if wav.dim() == 1 else wav
        else:
            audio_tensor = torch.from_numpy(wav).unsqueeze(0)
        
        buffer = io.BytesIO()
        torchaudio.save(buffer, audio_tensor, sample_rate, format="wav")
        audio_bytes = buffer.getvalue()
        
        print(f"[{requestID}] STS generation completed. Audio bytes: {len(audio_bytes)}, Sample rate: {sample_rate}")
        return audio_bytes, sample_rate
        
    except Exception as e:
        print(f"[{requestID}] Error during STS generation: {e}")
        raise e


if __name__ == "__main__":
    async def main():
        text = "How do you feel about this?"
        audio = "testing/W8i19O5P6L.wav"
        base64_audio = encode_audio_base64(audio)
        saved_audio_path = save_temp_audio(base64_audio, "request224", "speech")
        audio_conv = convertToAudio(saved_audio_path, "request224")
        requestID = "request123"
        system = None
        voice = None

        audio_bytes, sample_rate = await generate_sts(text, audio_conv, requestID, system, voice)
        with open(f"{requestID}.wav", "wb") as f:
            f.write(audio_bytes)
        print(f"Generated audio saved as {requestID}.wav with sample rate {sample_rate}")
    
    asyncio.run(main())