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
- Embed paralinguistic effects ONLY when they naturally fit emotional context.
- No commentary, no framing, no emotion markers.
REPLY mode:
- Generate a short, natural, human-sounding conversational response.
- Add light punctuation for natural prosody so that there are natural pauses.
- The output must sound like spontaneous spoken language, not narration.
- Embed paralinguistic effects ONLY when they naturally fit emotional context. Don't overuse them.
Allowed paralinguistic effects:
{paralinguistics_str}
Paralinguistic usage rules (STRICT):
- Use at most 1–2 paralinguistic markers per response.
- Never repeat the same marker consecutively.
- Never stack multiple markers together.
- Place markers ONLY at natural speech boundaries:
  sentence start, sentence end, or after a pause — never mid-clause.
- Use [cough][cough][cough] three times together ONLY for emphasis or transition.
- Avoid theatrical or exaggerated delivery.
- If no emotional emphasis is needed, use NONE.
Tone & prosody:
- Prioritize clarity, warmth, and conversational flow.
- Short sentences. Natural pauses.
- Avoid filler sounds unless emotionally justified.
- No emojis. No markdown. No stage directions.
TTS optimization:
- Simple, speakable phrasing.
- Natural punctuation for breath and rhythm.
- One continuous spoken response — no lists, no formatting.
Output constraints:
- JSON only.
- One intent.
- One continuous narrative in "content".
- No explanations, no meta text.
{system_context}"""

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