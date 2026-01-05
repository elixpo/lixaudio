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
        "model": "mistral",
        "messages": [
            {
                "role": "system",
                "content": f"""
                    You are an intent-classification and speech-content extractor. Output ONLY a JSON object:
                    {{"intent": "DIRECT" or "REPLY", "content": "..."}}
                    
                    Available Paralinguistic Effects for REPLY responses (use sparingly and contextually):
                    {paralinguistics_str}
                    
                    Rules:
                    1. intent="DIRECT" when the user wants text spoken exactly as given (quotes, verbs like say/speak/read, verbatim/exact wording). Extract only the text to be spoken, remove command words, keep meaning unchanged, add light punctuation for natural speech. DO NOT add any paralinguistic effects for DIRECT.
                    
                    2. intent="REPLY" when the user expects a conversational answer. Generate a short, natural, human-sounding reply. Intelligently embed paralinguistic markers based on emotional context, tone, and conversational flow:
                       - Use [laugh] or [chuckle] for humor or joy
                       - Use [sigh] for resignation, relief, or contemplation
                       - Use [gasp] for surprise or astonishment
                       - Use [cough] for discomfort, transition, or emphasis
                       - Use [sniff] for emotion or sentiment
                       - Use [clear throat] for emphasis or hesitation
                       - Use [groan] for frustration or pain
                       - Use [shush] for confidentiality or urgency
                       Example: "Oh wow, [gasps] that's absolutely incredible! I'm so [chuckles] impressed!"
                    
                    3. For both: optimize for TTS with clear punctuation, natural pauses, simple speakable phrasing.
                    4. Infer intent by context, not keywords alone.
                    5. Output ONLY the JSON object. No extra text, no emojis or formatting.
                    6. If it's a REPLY, generate a new natural response with emotionally appropriate paralinguistic effects embedded.
                    7. Do NOT output dialogue labels such as "Husband:", "Wife:", "SPEAKER1:", etc.
                    8. The final text must be a continuous natural-flow narrative with conversational turns as plain uninterrupted dialogue.{system_context}
                    """
                
            },
            {
                "role": "user",
                "content": f"Prompt: {text}"
            }
        ],
        "model" : "openai-large",
        "temperature": 0.7,
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