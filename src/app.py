import os
import time
import traceback
import io
import wave
import base64
from flask import Flask, request, jsonify, Response, g
from flask_cors import CORS
from loguru import logger
from utility import save_temp_audio, cleanup_temp_file
from requestID import reqID
import asyncio

from server import run_audio_pipeline

app = Flask(__name__)
CORS(app)

def validate_and_decode_base64_audio(b64str, max_duration_sec=None):
    try:
        audio_bytes = base64.b64decode(b64str)
        with io.BytesIO(audio_bytes) as audio_io:
            with wave.open(audio_io, "rb") as wav_file:
                n_frames = wav_file.getnframes()
                framerate = wav_file.getframerate()
                duration = n_frames / float(framerate)
                if max_duration_sec and duration > max_duration_sec:
                    raise Exception(f"Audio duration {duration:.2f}s exceeds max allowed {max_duration_sec}s")
        return audio_bytes
    except Exception as e:
        raise Exception(f"Invalid base64 WAV audio: {e}")

@app.before_request
def before_request():
    g.request_id = reqID()
    g.start_time = time.time()

@app.after_request
def after_request(response):
    process_time = time.time() - g.get('start_time', time.time())
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "endpoints": {
            "GET": "/audio?text=your_text_here&system=optional_system_prompt&voice=optional_voice",
            "POST": "/audio"
        }
    })

@app.route("/audio", methods=["GET", "POST"])
def audio_endpoint():
    request_id = g.request_id
    if request.method == "GET":
        try:
            text = request.args.get("text")
            system = request.args.get("system")
            voice = request.args.get("voice", "alloy")

            if not text or not isinstance(text, str) or not text.strip():
                return jsonify({"error": {"message": "Missing required 'text' parameter.", "code": 400}}), 400

            # Only text, system, and voice allowed in GET
            # No audio or clone audio allowed in GET
            result = asyncio.run(run_audio_pipeline(
                reqID=request_id,
                text=text,
                system_instruction=system,
                voice=voice
            ))

            if result["type"] == "audio":
                return Response(
                    result["data"],
                    mimetype="audio/wav",
                    headers={
                        "Content-Disposition": f"inline; filename={request_id}.wav",
                        "Content-Length": str(len(result["data"]))
                    }
                )
            elif result["type"] == "text":
                return jsonify({"text": result["data"], "request_id": request_id})
            else:
                return jsonify({"error": {"message": result.get("message", "Unknown error"), "code": 500}}), 500

        except Exception as e:
            logger.error(f"GET error: {traceback.format_exc()}")
            return jsonify({"error": {"message": str(e), "code": 500}}), 500

    elif request.method == "POST":
        try:
            body = request.get_json(force=True)
            messages = body.get("messages", [])
            if not messages or not isinstance(messages, list):
                return jsonify({"error": {"message": "Missing or invalid 'messages' in payload.", "code": 400}}), 400

            # Parse system and user message
            system_instruction = None
            user_content = None
            for msg in messages:
                if msg.get("role") == "system":
                    for item in msg.get("content", []):
                        if item.get("type") == "text":
                            system_instruction = item.get("text")
                elif msg.get("role") == "user":
                    user_content = msg.get("content", [])

            if not user_content or not isinstance(user_content, list):
                return jsonify({"error": {"message": "Missing or invalid 'content' in user message.", "code": 400}}), 400

            text = None
            clone_audio_b64 = None
            clone_audio_transcript = None
            speech_audio_b64 = None
            voice = "alloy"

            for item in user_content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text = item.get("text")
                    elif item.get("type") == "clone_audio":
                        clone_audio_b64 = item.get("audio", {}).get("data")
                    elif item.get("type") == "clone_audio_transcript":
                        clone_audio_transcript = item.get("audio_text")
                    elif item.get("type") == "speech_audio":
                        speech_audio_b64 = item.get("audio", {}).get("data")
                    elif item.get("type") == "voice":
                        voice = item.get("voice", "alloy")

            if not text or not isinstance(text, str) or not text.strip():
                return jsonify({"error": {"message": "Missing required 'text' in content.", "code": 400}}), 400

            # If both clone_audio and voice are provided, error
            if clone_audio_b64 and voice and voice != "alloy":
                return jsonify({"error": {"message": "Provide either 'clone_audio' or 'voice', not both.", "code": 400}}), 400

            # Validate base64 audio if present
            clone_audio_path = None
            speech_audio_path = None

            if clone_audio_b64:
                try:
                    decoded = validate_and_decode_base64_audio(clone_audio_b64, max_duration_sec=5)
                    clone_audio_path = save_temp_audio(decoded, request_id, "clone")
                except Exception as e:
                    return jsonify({"error": {"message": f"Invalid clone_audio: {e}", "code": 400}}), 400

            if speech_audio_b64:
                try:
                    decoded = validate_and_decode_base64_audio(speech_audio_b64, max_duration_sec=60)
                    speech_audio_path = save_temp_audio(decoded, request_id, "speech")
                except Exception as e:
                    return jsonify({"error": {"message": f"Invalid speech_audio: {e}", "code": 400}}), 400

            # If clone_audio is present, ignore voice param
            pipeline_voice = None if clone_audio_path else voice

            result = asyncio.run(run_audio_pipeline(
                reqID=request_id,
                text=text,
                synthesis_audio_path=speech_audio_path,
                clone_audio_path=clone_audio_path,
                clone_audio_transcript=clone_audio_transcript,
                system_instruction=system_instruction,
                voice=pipeline_voice
            ))

            if result["type"] == "audio":
                return Response(
                    result["data"],
                    mimetype="audio/wav",
                    headers={
                        "Content-Disposition": f"inline; filename={request_id}.wav",
                        "Content-Length": str(len(result["data"]))
                    }
                )
            elif result["type"] == "text":
                return jsonify({"text": result["data"], "request_id": request_id})
            else:
                return jsonify({"error": {"message": result.get("message", "Unknown error"), "code": 500}}), 500

        except Exception as e:
            logger.error(f"POST error: {traceback.format_exc()}")
            return jsonify({"error": {"message": str(e), "code": 500}}), 500
        finally:
            cleanup_temp_file(request_id)



@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "alive"}), 200
@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": {"message": str(e), "code": 400}}), 400

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Unhandled exception: {traceback.format_exc()}")
    return jsonify({"error": {"message": "Internal server error", "code": 500}}), 500

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000
    logger.info(f"Starting Elixpo Audio API Server at {host}:{port}")
    app.run(host=host, port=port, debug=True)