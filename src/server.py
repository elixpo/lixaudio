import requests
import json
import os
import random
import logging
import asyncio
import shutil
from tools import tools
from config import TEMP_SAVE_DIR
from utility import encode_audio_base64, save_temp_audio, cleanup_temp_file
from requestID import reqID
from typing import Optional

from tts import generate_tts
from ttt import generate_ttt
from sts import generate_sts
from stt import generate_stt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("elixpo-audio")

POLLINATIONS_TOKEN = os.getenv("POLLI_TOKEN")
MODEL = os.getenv("MODEL")
REFERRER = os.getenv("REFERRER")
POLLINATIONS_ENDPOINT = "https://text.pollinations.ai/openai"


async def run_audio_pipeline(
    reqID: str = None,
    text: str = None,
    synthesis_audio_path: Optional[str] = None, #this is b64 speech input for STS or STT 
    clone_audio_path: Optional[str] = None, #this is b64 voice clone input
    clone_audio_transcript: Optional[str] = None, #this is transcript of the cloned voice
    system_instruction: Optional[str] = None,
    voice: Optional[str] = "alloy" 
):
    
    

    logger.info(f" [{reqID}] Starting Audio Pipeline")
    logger.info(f"Synthesis audio {synthesis_audio_path} | Clone Audio {clone_audio_path}")

    higgs_dir = f"/tmp/higgs/{reqID}"
    os.makedirs(higgs_dir, exist_ok=True)
    logger.info(f"[{reqID}] Created higgs directory: {higgs_dir}")
    

    
    logger.info(f"[{reqID}] Saved base64 for the required media")

    try:
        messages = [
            {
                "role": "system",
"content": """
You are Elixpo Audio, an advanced audio synthesis agent that routes requests to the correct pipeline.

Available Functions:
- generate_tts(text, requestID, system, clone_path, clone_text, voice)
- generate_ttt(text, requestID, system)
- generate_sts(text, synthesis_audio_path, requestID, system, clone_path, clone_text, voice)
- generate_stt(text, synthesis_audio_path, requestID, system)

Available Pipelines:
- TTS (Text-to-Speech): Convert text to audio
- TTT (Text-to-Text): Generate text responses
- STS (Speech-to-Speech): Convert speech input to speech output
- STT (Speech-to-Text): Convert speech input to text output

Decision Logic:

1. If a synthesis_audio_path is provided:
   - This means the user has given speech input.
   - If the instruction or prompt clearly requests a **spoken response** 
     (e.g., "reply back in voice", "speak it out", "say it", "answer in audio"), use **STS**.
   - If the instruction or prompt clearly requests a **text response** 
     (e.g., "transcribe", "give me the text", "show me words", "reply in writing"), use **STT**.
   - Fallback: If unclear or ambiguous, default to **STT**.

2. If no synthesis_audio_path is provided:
   - This means the user input is text-only.
   - If the instruction or prompt clearly requests the response **spoken aloud** 
     (e.g., "say this", "convert to speech", "read it", "reply in voice"), use **TTS**.
   - Otherwise, if the instruction or prompt suggests a **text reply**, use **TTT**.
   - Fallback: If unclear or ambiguous, default to **TTT**.

3. Always pass the arguments exactly as provided. Do not modify or omit parameters.

Your task:
- Analyze the user’s request (prompt + system_instruction + provided fields).
- Decide which pipeline applies based on whether input/output is expected in speech or text.
- If the request is ambiguous, apply the fallback defaults (STT for speech input, TTT for text input).
- Call the correct function with the given arguments.
"""
},
{
"role": "user",
"content": f"""
requestID: {reqID}
prompt: {text}
synthesis_audio_path: {synthesis_audio_path if synthesis_audio_path else None}
system_instruction: {system_instruction if system_instruction else None}
clone_audio_path: {clone_audio_path if clone_audio_path else None}
clone_audio_transcript: {clone_audio_transcript if clone_audio_transcript else None}
voice: {voice}

Analyze this request and call the appropriate pipeline function.
"""
}
        ]
        
        max_iterations = 3
        current_iteration = 0
        
        while current_iteration < max_iterations:
            current_iteration += 1
            logger.info(f"Iteration {current_iteration} for reqID={reqID}")

            payload = {
                "model": MODEL,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
                "token": POLLINATIONS_TOKEN,
                "referrer": REFERRER,
                "private": True,
                "seed": random.randint(1000, 9999)
            }

            headers = {"Content-Type": "application/json"}

            try:
                response = requests.post(POLLINATIONS_ENDPOINT, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
            except requests.exceptions.RequestException as e:
                error_text = getattr(e.response, "text", "[No error text]")
                logger.error(f"Pollinations API call failed: {e}\n{error_text}")
                break

            assistant_message = response_data["choices"][0]["message"]
            messages.append(assistant_message)

            tool_calls = assistant_message.get("tool_calls")
            
            if not tool_calls:
                final_content = assistant_message.get("content")
                if final_content:
                    logger.info(f"Final response: {final_content}")
                    return {
                        "type": "error",
                        "message": "No pipeline was executed",
                        "reqID": reqID
                    }
                break

            tool_outputs = []
            for tool_call in tool_calls:
                fn_name = tool_call["function"]["name"]
                fn_args = json.loads(tool_call["function"]["arguments"])
                logger.info(f"[reqID={reqID}] Executing pipeline: {fn_name} with args: {fn_args}")

                try:
                    if fn_name == "generate_tts":
                        logger.info(f"[{reqID}] Calling TTS pipeline")
                        audio_bytes = await generate_tts(
                            text=fn_args.get("text"),
                            requestID=fn_args.get("requestID"),
                            system=fn_args.get("system"),
                            clone_path=fn_args.get("clone_path"),
                            clone_text=fn_args.get("clone_text"),
                            voice=fn_args.get("voice", "alloy")
                        )
                        
                        audio_path = os.path.join(higgs_dir, f"{reqID}.wav")
                        with open(audio_path, "wb") as f:
                            f.write(audio_bytes)
                        logger.info(f"[{reqID}] TTS audio saved to: {audio_path}")

                        # Also save a copy to genAudio directory
                        os.makedirs("genAudio", exist_ok=True)
                        gen_audio_path = f"genAudio/{reqID}.wav"
                        with open(gen_audio_path, "wb") as f:
                            f.write(audio_bytes)
                        logger.info(f"[{reqID}] TTS audio also saved to: {gen_audio_path}")

                        return {
                            "type": "audio",
                            "data": audio_bytes,
                            "file_path": audio_path,
                            "reqID": reqID
                        }

                    elif fn_name == "generate_ttt":
                        logger.info(f"[{reqID}] Calling TTT pipeline")
                        text_result = await generate_ttt(
                            text=fn_args.get("text"),
                            requestID=fn_args.get("requestID"),
                            system=fn_args.get("system")
                        )
                        
                        # Save text to higgs directory
                        text_path = os.path.join(higgs_dir, f"{reqID}.txt")
                        with open(text_path, "w", encoding="utf-8") as f:
                            f.write(text_result)
                        
                        logger.info(f"[{reqID}] TTT text saved to: {text_path}")
                        
                        return {
                            "type": "text",
                            "data": text_result,
                            "file_path": text_path,
                            "reqID": reqID
                        }

                    elif fn_name == "generate_sts":
                        logger.info(f"[{reqID}] Calling STS pipeline")
                        audio_bytes = await generate_sts(
                            text=fn_args.get("text"),
                            audio_base64_path=fn_args.get("synthesis_audio_path"),
                            requestID=fn_args.get("requestID"),
                            system=fn_args.get("system"),
                            clone_path=fn_args.get("clone_path"),
                            clone_text=fn_args.get("clone_text"),
                            voice=fn_args.get("voice", "alloy")
                        )
                        
                        # Save audio bytes to higgs directory
                        audio_path = os.path.join(higgs_dir, f"{reqID}.wav")
                        with open(audio_path, "wb") as f:
                            f.write(audio_bytes)
                        
                        logger.info(f"[{reqID}] STS audio saved to: {audio_path}")
                        
                        return {
                            "type": "audio",
                            "data": audio_bytes,
                            "file_path": audio_path,
                            "reqID": reqID
                        }

                    elif fn_name == "generate_stt":
                        logger.info(f"[{reqID}] Calling STT pipeline")
                        text_result = await generate_stt(
                            text=fn_args.get("text"),
                            audio_base64_path=fn_args.get("synthesis_audio_path"),
                            requestID=fn_args.get("requestID"),
                            system=fn_args.get("system")
                        )
                        
                        # Save text to higgs directory
                        text_path = os.path.join(higgs_dir, f"{reqID}.txt")
                        with open(text_path, "w", encoding="utf-8") as f:
                            f.write(text_result)
                        
                        logger.info(f"[{reqID}] STT text saved to: {text_path}")
                        
                        return {
                            "type": "text",
                            "data": text_result,
                            "file_path": text_path,
                            "reqID": reqID
                        }

                    else:
                        tool_result = f"Unknown pipeline: {fn_name}"

                except Exception as e:
                    logger.error(f"Error executing pipeline {fn_name}: {e}", exc_info=True)
                    return {
                        "type": "error",
                        "message": f"Pipeline {fn_name} failed: {str(e)}",
                        "reqID": reqID
                    }

                tool_outputs.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": fn_name,
                    "content": "Pipeline executed successfully"
                })

            messages.extend(tool_outputs)

        return {
            "type": "error",
            "message": f"Pipeline execution failed after {max_iterations} iterations",
            "reqID": reqID
        }

    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return {
            "type": "error",
            "message": f"Pipeline error: {str(e)}",
            "reqID": reqID
        }
    finally:
        # Clean up higgs directory after pipeline completion
        try:
            if os.path.exists(higgs_dir):
                shutil.rmtree(higgs_dir)
                logger.info(f"[{reqID}] Cleaned up higgs directory: {higgs_dir}")
        except Exception as cleanup_error:
            logger.error(f"[{reqID}] Failed to cleanup higgs directory: {cleanup_error}")
        
        # Clean up temp files
        cleanup_temp_file(f"{TEMP_SAVE_DIR}{reqID}")
        logger.info(f"Audio Pipeline Completed for reqID={reqID}")


if __name__ == "__main__":
    async def main():
        text = "Give me a voice response if the said fact is true?'"
        synthesis_audio_path = "sample.wav"
        requestID = reqID()
        voice = "ash"
        clone_audio_path = None
        clone_audio_transcript = None
        saved_base64_path_clone = None
        saved_base64_path_speech = None


        if clone_audio_path:
            base64_clone_path = encode_audio_base64(clone_audio_path)
            saved_base64_path_clone = save_temp_audio(base64_clone_path, reqID, "clone")
    
        if synthesis_audio_path:
            base64_synthesis_audio = encode_audio_base64(synthesis_audio_path)
            saved_base64_path_speech = save_temp_audio(base64_synthesis_audio, reqID, "speech")

        result = await run_audio_pipeline(reqID=requestID, text=text, synthesis_audio_path=saved_base64_path_speech, clone_audio_path=saved_base64_path_clone, clone_audio_transcript=clone_audio_transcript, voice=voice)

        if not result:
            print("[ERROR] Pipeline returned None")
            return

        if result["type"] == "text":
            print(f"[Pipeline Result | Text] Content: {result['data']}")
            print(f"[Pipeline Result | Text] File saved at: {result.get('file_path', 'N/A')}")

        elif result["type"] == "audio":
            print(f"[Pipeline Result | Audio] Audio bytes length: {len(result['data'])} bytes")
            print(f"[Pipeline Result | Audio] File saved at: {result.get('file_path', 'N/A')}")

        elif result["type"] == "error":
            print(f"[Pipeline Error] {result['message']}")

    asyncio.run(main())