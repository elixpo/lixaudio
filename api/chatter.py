import torchaudio as ta
import torch
from pathlib import Path
from chatterbox.tts_turbo import ChatterboxTurboTTS
import time
# Set cache directory for the model
cache_dir = "model_cache"
Path(cache_dir).mkdir(exist_ok=True)

start_time = time.time()
# Load the Turbo model
model = ChatterboxTurboTTS.from_pretrained(device="cuda", cache_dir=cache_dir)
# Generate with Paralinguistic Tags
print(f"Model loaded in {time.time() - start_time:.2f} seconds.")
text = "[cough] [cough] [cough] Oh damn! [sniff] I think I'm coming down with something [clear throat]"

start_time = time.time()

wav = model.generate(
    text,
    top_p=0.95,
    temperature=0.8,
    top_k=1000,
    repetition_penalty=1.2,
    audio_prompt_path="voices_b64/raw_wav/ash.wav"
    )
print(f"Audio generated in {time.time() - start_time:.2f} seconds.")
ta.save("test-turbo.wav", wav, model.sr)