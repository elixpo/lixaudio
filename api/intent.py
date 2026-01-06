from loguru import logger
import requests
from typing import Optional
from dotenv import load_dotenv
import os
import asyncio
from config import paralinguistics_tags, POLLINATIONS_ENDPOINT_TEXT

load_dotenv()


async def getContentRefined(text: str, system: Optional[str] = None, max_tokens: Optional[int] = 3000) -> dict:
    logger.info(f"Classifying intent and extracting content for prompt: {text} with max tokens: {max_tokens}")

    paralinguistics_list = list(paralinguistics_tags.values())
    paralinguistics_str = ", ".join(paralinguistics_list)
    
    system_context = ""
    if system:
        system_context = f"\nUser's System Instruction/Style: {system}"
        
    payload = {
        "messages": [
            {
                "role": "system",
                "content": f"""
                    You are an intent-classification and speech-content extractor. Output ONLY a JSON object:
                    {{"intent": "DIRECT" or "REPLY", "content": "..."}}
                    By default we shall make a reply type until the user specifies in the prompt for verbatim speech.
                    Understand the verbatim speech request in general and switch to DIRECT only when explicitly requested.
                    Available Paralinguistic Effects for REPLY responses (use liberally and contextually):
                    {paralinguistics_str}
                    DIRECT: User wants text spoken exactly as given. Extract only the text to be spoken, remove command words, keep meaning unchanged, add light punctuation for natural speech. DO NOT add paralinguistic effects for DIRECT.
                    REPLY: Generate a short, natural, human-sounding conversational answer. Embed paralinguistic markers based on emotional context and tone:
                       - [laugh], [chuckle], [giggle] for humor, joy, amusement
                       - [sigh], [exhale] for resignation, relief, contemplation
                       - [gasp], [gasp] for surprise, astonishment, shock
                       - [cough] [cough] [cough] for emphasis, discomfort, transition
                       - [sniff], [snffle] for emotion, sentiment, sadness
                       - [clear throat] for emphasis, hesitation, authority
                       - [groan], [ugh] for frustration, pain, annoyance
                       - [shush] for confidentiality, urgency
                       - [whisper] for intimacy, secrecy
                       Always use 3 coughs simultaneously for emphasis and use more of the other effects to create a lively, engaging speech output.
                    For both: optimize for TTS with clear punctuation, natural pauses, simple speakable phrasing.
                    Infer intent by context, not keywords alone. Output ONLY the JSON object. No extra text, no emojis.
                    If REPLY, generate a new natural response with emotionally appropriate paralinguistic effects embedded throughout.
                    The final text must be a continuous natural-flow narrative with conversational turns as plain uninterrupted dialogue.{system_context}
                    """
                
            },
            {
                "role": "user",
                "content": f"Prompt: {text}"
            }
        ],
        "model" : "gemini-fast",
        "temperature": 0.2,
        "stream": False,
        "private": True,
        "max_tokens": max_tokens,
        "json": True,
    }
    header = {
        "Content-Type": "application/json",
        "Authorization" : f"Bearer {os.getenv('POLLI_TOKEN')}"
    }

    try:
        response = requests.post(POLLINATIONS_ENDPOINT_TEXT, json=payload, headers=header, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Request failed: {response.status_code}, {response.text}")

        data = response.json()
        try:
            reply = data["choices"][0]["message"]["content"]
            import json as pyjson
            result = pyjson.loads(reply)
            required_fields = ["intent", "content"]

            for field in required_fields:
                assert field in result
        except Exception as e:
            raise RuntimeError(f"Unexpected response format: {data}") from e

        logger.info(f"Intent and content: {result}")
        return result

    except requests.exceptions.Timeout:
        logger.warning("Timeout occurred in getContentRefined, returning default DIRECT.")
        return {"intent": "DIRECT", "content": text}


if __name__ == "__main__":
    async def main():
        test_text = "Wow, that was an amazing performance! How did you manage to pull that off?"
        print(f"\nTesting: {test_text}")
        result = await getContentRefined(test_text)
        print(f"Intent: {result.get('intent')}")
        print(f"Content: {result.get('content')}")
        print("-" * 50)

    asyncio.run(main())