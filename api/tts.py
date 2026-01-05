from utility import cleanup_temp_file, validate_and_decode_base64_audio
from voiceMap import VOICE_BASE64_MAP
import asyncio
from typing import Optional
from multiprocessing.managers import BaseManager
import os
import threading
import time
import torch
import torchaudio
import io 
import numpy as np
import time

class ModelManager(BaseManager): pass
ModelManager.register("Service")
manager = ModelManager(address=("localhost", 6000), authkey=b"secret")
manager.connect()
service = manager.Service()

async def generate_tts(text: str, requestID: str, system: Optional[str] = None, voice: Optional[str] = "alloy") -> tuple:
    clone_path = None
    if voice and not VOICE_BASE64_MAP.get(voice):
        try:
            with open(voice, "r") as f:
                audio_data = f.read()
                if validate_and_decode_base64_audio(audio_data):
                    clone_path = voice
        except Exception as e:
            print(f"[{requestID}] Failed to load voice from path {voice}: {e}. Falling back to alloy.")
            clone_path = VOICE_BASE64_MAP.get("alloy")
    elif voice and VOICE_BASE64_MAP.get(voice):
        clone_path = VOICE_BASE64_MAP.get(voice)
    else:
        clone_path = VOICE_BASE64_MAP.get("alloy")
    
    try:
        print(f"[{requestID}] Generating TTS audio with voice: {voice}")
        wav, sample_rate = service.speechSynthesis(chatTemplate=text, audio_prompt_path=clone_path)
        
        if wav is None:
            raise RuntimeError("Audio generation failed - GPU out of memory or other error")
        
        if isinstance(wav, torch.Tensor):
            audio_numpy = wav.cpu().numpy()
        else:
            audio_numpy = wav
        
        print(f"[{requestID}] TTS generation completed. Audio shape: {audio_numpy.shape}, Sample rate: {sample_rate}")
        return audio_numpy, sample_rate
        
    except Exception as e:
        print(f"[{requestID}] Error during TTS generation: {e}")
        raise e
    
    
if __name__ == "__main__":
    class ModelManager(BaseManager): pass
    ModelManager.register("Service")
    manager = ModelManager(address=("localhost", 6000), authkey=b"secret")
    manager.connect()
    service = manager.Service()

    async def main():
        text = "She sat alone in the quiet room, clutching a faded photograph. Rain tapped gently against the window, echoing the ache in her heart. Years had passed since she lost him, but the emptiness lingered, growing heavier with each memory. She whispered his name, hoping for an answer that would never come. The world moved on, but her world had stopped, frozen in the moment he said goodbye."
        requestID = "request123"
        system = None
        voice = "ash"
        clone_text = None
        
        def cleanup_cache():
            while True:
                try:
                    service.cleanup_old_cache_files()
                except Exception as e:
                    print(f"Cleanup error: {e}")

                time.sleep(600)

        cleanup_thread = threading.Thread(target=cleanup_cache, daemon=True)
        cleanup_thread.start()
        cache_name = service.cacheName(text)
        # if os.path.exists(f"genAudio/{cache_name}.wav"):
        #     print(f"Cache hit: genAudio/{cache_name}.wav already exists.")
        #     return
        
        audio_numpy, audio_sample = await generate_tts(text, requestID, system, clone_text, voice)
        audio_tensor = torch.from_numpy(audio_numpy).unsqueeze(0)
        torchaudio.save(f"{cache_name}.wav", audio_tensor, audio_sample)
        torchaudio.save(f"genAudio/{cache_name}.wav", audio_tensor, audio_sample)
        print(f"Audio saved as {cache_name}.wav")

    asyncio.run(main())