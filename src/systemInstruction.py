import requests
from dotenv import load_dotenv
import os 
from loguru import logger
import asyncio


load_dotenv()


async def generate_higgs_system_instruction(text: str) -> str:
    logger.info(f"Generating Higgs system instruction for text: {text}")
    base_instruction = (
    """
You are a system instruction generator for a speech synthesis model called Higgs. 
Your job is to transform the user’s prompt into a cinematic voice performance script. 

Inside your response, provide:
- A vivid scene description adapted from the user’s text.
- Explicit emotional and tonal guidance (joy, suspense, calm, intensity, etc.).
- Performance notes: pacing, pauses, breathing, emphasis.
- The overall pacing should be **moderate-fast and energetic**, like natural storytelling with excitement.
- Avoid unnecessary pauses or artificial stresses. If pauses are used, they must feel natural and purposeful.
- The vibe should always be fresh, flowing, and engaging — never flat or overly dramatic.

Always respond with this structure: 
(
"You are a voice synthesis engine. Speak the user’s text exactly and only as written. Do not add extra words, introductions, or confirmations"
"Apply the emotions as written in the user prompt"
"Maintain a moderate-fast, energetic pacing with natural variation and excitement"
"Do not insert unnecessary pauses or stress — keep delivery smooth and natural"
"Generate audio following instruction."
"<|scene_desc_start|>\n"
"Instruction goes here\n"
"<|scene_desc_end|>"
)
    """
)




    payload = {
        "model": "mistral",
        "messages": [
            {"role": "system", "content": base_instruction},
            {
                "role": "user",
                "content": (
                    f"""User prompt: {text}"""
                )
            }
        ],
        "temperature": 0.7,
        "stream": False,
        "private": True,
        "token": os.getenv("POLLI_TOKEN"),
        "referrer": "elixpoart",
        "max_tokens": 100,
        "seed": 42
    }
    try:
        response = requests.post("https://text.pollinations.ai/openai", json=payload, timeout=30)
        if response.status_code != 200:
            raise RuntimeError(f"Request failed: {response.status_code}, {response.text}")

        data = response.json()
        try:
            system_instruction: str  = data["choices"][0]["message"]["content"]
            if "---" in system_instruction and "**Sponsor**" in system_instruction:
                sponsor_start = system_instruction.find("---")
                if sponsor_start != -1:
                    sponsor_section = system_instruction[sponsor_start:]
                    if "**Sponsor**" in sponsor_section:
                        system_instruction = system_instruction[:sponsor_start].strip()
            
        except Exception as e:
            raise RuntimeError(f"Unexpected response format: {data}") from e

        return system_instruction.strip()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except requests.exceptions.Timeout:
        return f"""
(
"You are a voice synthesis engine. Speak the user’s text exactly and only as written. Do not add extra words, introductions, or confirmations\n"
"Apply the emotions as written in the user prompt\n"
"Generate audio following instruction.\n"
"<|scene_desc_start|>\n"

"<|scene_desc_end|>"
)
        """


if __name__ == "__main__":
    async def main():
        user_prompt = "A tense courtroom drama where the verdict is about to be announced."

        system_instruction = await generate_higgs_system_instruction(user_prompt)
        print("\n--- Generated Higgs System Instruction ---\n")
        print(system_instruction)
    asyncio.run(main())