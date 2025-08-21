from systemInstruction import generate_higgs_system_instruction
from utility import encode_audio_base64, save_temp_audio
from templates import create_speaker_chat
from synthesis import synthesize_speech
from stt import generate_stt
from loguru import logger
from voiceMap import VOICE_BASE64_MAP
from typing import Optional
import asyncio
from load_models import audio_model


async def generate_sts(text: str, audio_base64_path: str, requestID: str, system: Optional[str] = None, clone_path: Optional[str] = None, clone_text: Optional[str] = None, voice: Optional[str] = "alloy") -> str:
    if clone_path is None:
        if(voice):
            load_audio_path = VOICE_BASE64_MAP.get(voice)
            base64 = encode_audio_base64(load_audio_path)    
            clone_path = base64
    if system is None:
        system = await generate_higgs_system_instruction(text)
    else:
        system = f"""
        "You are a voice synthesis engine. Speak the user’s text exactly and only as written. Do not add extra words, introductions, or confirmations.\n"
        "Apply the emotions as written in the user prompt.\n"
        "Generate audio following instruction.\n"
        "<|scene_desc_start|>\n"
            {system}\n
        "<|scene_desc_end|>"
        """
    pipelined_transcription = await generate_stt(text, audio_base64_path, requestID, system)
    chatTemplate = create_speaker_chat(
        text=pipelined_transcription,
        requestID=requestID,
        system=system,
        clone_audio_path=clone_path,
        clone_audio_transcript=clone_text
    )
    audio_bytes = await synthesize_speech(chatTemplate, higgs_engine=audio_model)
    return audio_bytes


if __name__ == "__main__":
    async def main():
        text = "Is this fact true? Tell me more about it!"
        audio = "sample.wav"
        base264_audio = encode_audio_base64(audio)
        saved_audio_path = save_temp_audio(base264_audio, "request224", "speech")
        requestID = "request123"
        system = None
        clone_path = None
        clone_text = None
        voice = "ash"

        audio_bytes = await generate_sts(text, saved_audio_path, requestID, system, clone_path, clone_text, voice)
        with open("output_sts.wav", "wb") as f:
            f.write(audio_bytes)
        print("Audio saved as output_sts.wav")
    asyncio.run(main())