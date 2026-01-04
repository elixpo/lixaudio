import torchaudio as ta
import torch
from pathlib import Path
from chatterbox.tts_turbo import ChatterboxTurboTTS

# Set cache directory for the model
cache_dir = "model_cache"
Path(cache_dir).mkdir(exist_ok=True)

# Load the Turbo model
model = ChatterboxTurboTTS.from_pretrained(device="cuda", cache_dir=cache_dir)
# Generate with Paralinguistic Tags

text = "Wow, this is absolutely amazing! [laugh] I cannot believe how incredibly awesome this is! [excited] You know, life is just so wonderfully unpredictable and full of surprises! [cough] Sometimes I just want to jump up and down with pure joy! [laugh] This whole experience has been such a delightful roller coaster of emotions and fun! [cough] I'm literally over the moon right now!"

# Generate audio (requires a reference clip for voice cloning)
wav = model.generate(
    text,
    top_p=0.95,
    temperature=0.8,
    top_k=1000,
    repetition_penalty=1.2,
    audio_prompt_path="voices_b64/default_wav/ash.wav",  # Path to a reference audio file
    )

ta.save("test-turbo.wav", wav, model.sr)