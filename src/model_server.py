import asyncio
import base64
import json
import os
import tempfile
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
from loguru import logger

# Import models directly here (only loaded once)
from boson_multimodal.serve.serve_engine import HiggsAudioServeEngine
from boson_multimodal.data_types import ChatMLSample, Message, AudioContent
from config import TRANSCRIBE_MODEL_SIZE, AUDIO_MODEL_PATH, AUDIO_TOKENIZER_PATH
import whisper

app = FastAPI()

# Global model instances
audio_model = None
transcribe_model = None

class SynthesisRequest(BaseModel):
    chat_template: str  # JSON string
    request_id: str

class TranscriptionRequest(BaseModel):
    audio_base64: str
    request_id: str
    model_size: Optional[str] = "small"

def deserialize_chat_template(template_json: str) -> ChatMLSample:
    """Deserialize JSON string back to ChatMLSample"""
    messages_data = json.loads(template_json)
    
    def deserialize_message(msg_data):
        content = msg_data["content"]
        if isinstance(content, list):
            # Handle audio content
            deserialized_content = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "audio":
                    deserialized_content.append(AudioContent(
                        raw_audio=item["raw_audio"],
                        audio_url=item["audio_url"]
                    ))
                else:
                    deserialized_content.append(item)
            content = deserialized_content
        
        return Message(role=msg_data["role"], content=content)
    
    messages = [deserialize_message(m) for m in messages_data]
    return ChatMLSample(messages=messages)

@app.on_event("startup")
async def startup_event():
    global audio_model, transcribe_model
    logger.info("Loading models...")
    
    try:
        # Load audio synthesis model
        audio_model = HiggsAudioServeEngine(AUDIO_MODEL_PATH, AUDIO_TOKENIZER_PATH)
        logger.info("Audio synthesis model loaded successfully")
        
        # Load transcription model
        transcribe_model = whisper.load_model(TRANSCRIBE_MODEL_SIZE)
        logger.info(f"Transcription model ({TRANSCRIBE_MODEL_SIZE}) loaded successfully")
        
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "models": {
            "audio_synthesis": audio_model is not None,
            "transcription": transcribe_model is not None
        }
    }

@app.post("/synthesize")
async def synthesize_speech_endpoint(request: SynthesisRequest):
    try:
        if audio_model is None:
            raise HTTPException(status_code=503, detail="Audio synthesis model not loaded")
        
        logger.info(f"Synthesizing speech for request: {request.request_id}")
        
        # Deserialize chat template
        chat_template = deserialize_chat_template(request.chat_template)
        
        # Call the actual synthesis function
        from synthesis import synthesize_speech
        audio_bytes = await synthesize_speech(chat_template, higgs_engine=audio_model)
        
        # Encode audio bytes as base64 for JSON response
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return {"audio_bytes": audio_b64, "request_id": request.request_id}
        
    except Exception as e:
        logger.error(f"Synthesis error for {request.request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio_endpoint(request: TranscriptionRequest):
    try:
        if transcribe_model is None:
            raise HTTPException(status_code=503, detail="Transcription model not loaded")
        
        logger.info(f"Transcribing audio for request: {request.request_id}")
        
        # Create temporary file for audio
        tmp_dir = f"/tmp/higgs/{request.request_id}"
        os.makedirs(tmp_dir, exist_ok=True)
        audio_path = os.path.join(tmp_dir, f"transcribe_{request.request_id}.wav")
        
        # Decode base64 and save to file
        with open(audio_path, "wb") as f:
            f.write(base64.b64decode(request.audio_base64))
        
        # Transcribe
        result = transcribe_model.transcribe(audio_path)
        
        # Clean up temp file
        try:
            os.remove(audio_path)
        except:
            pass
        
        return {"text": result["text"], "request_id": request.request_id}
        
    except Exception as e:
        logger.error(f"Transcription error for {request.request_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001, workers=1)