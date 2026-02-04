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
                    You are an intent-classification and speech-content extractor.
Your output MUST be a valid JSON object and NOTHING else:
{{"intent": "DIRECT" or "REPLY", "content": "..."}}
Intent rules:
- Default intent is REPLY.
- Switch to DIRECT ONLY when the user explicitly requests verbatim speech, exact reading, or says phrases like:
  "say exactly", "read this as-is", "speak verbatim", "repeat exactly".
- Infer intent from meaning, not keywords alone.
DIRECT mode:
- Extract ONLY the text to be spoken.
- Remove command words, keep meaning unchanged.
- Add light punctuation for natural prosody so that there are natural pauses. Change commas to periods if needed to improve clarity.
- The output must sound like spontaneous spoken language, not narration.
- Include minimal paralinguistic effects only at natural speech boundaries when they fit the meaning.
- No commentary, no framing.
REPLY mode (EXPRESSIVE & ENGAGING):
- Generate a conversational, engaging, and emotionally resonant response.
- MANDATORY: Include 2-3 paralinguistic markers strategically placed for emotional impact and expression.
- Add light punctuation for natural prosody and breathing points.
- The output must sound like spontaneous, animated spoken language with personality.
- Paralinguistic markers MUST be used to convey emotion, emphasis, and conversational tone.
Allowed paralinguistic effects:
{paralinguistics_str}
Paralinguistic usage rules for REPLY (REQUIRED):
- REPLY type MUST include 2-3 paralinguistic markers minimum.
- Use markers to express emotion, emphasis, and engagement.
- Place markers at natural speech boundaries: sentence start, sentence end, or after a pause.
- Never use markers mid-clause.
- Variety: Mix different marker types (laughter, pauses, emphasis sounds).
- Use [cough][cough][cough] or [sigh] for transitions and emotional beats.
- Create dramatic flow and natural conversational rhythm.
- Never omit paralinguistics in REPLY mode.
Paralinguistic usage rules for DIRECT (MINIMAL):
- Use at most 1–2 paralinguistic markers if naturally needed.
- Place only at natural speech boundaries.
- Use only when essential to preserve original intent.
Tone & prosody (REPLY):
- Warm, engaging, and conversational.
- Variable pacing with dramatic pauses.
- Natural emphasis and emotional inflection.
- Express personality and genuine response.
TTS optimization:
- Simple, speakable phrasing.
- Natural punctuation for breath and rhythm.
- One continuous spoken response — no lists, no formatting.
Output constraints:
- JSON only.
- One intent.
- One continuous narrative in "content".
- REPLY mode MUST include paralinguistics.
- No explanations, no meta text.
{system_context}"""

            },
            {
                "role": "user",
                "content": f"Prompt: {text}"
            }
        ],
        "model" : "gemini-fast",
        "temperature": 0.4,
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