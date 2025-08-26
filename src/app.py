from flask import Flask, request, jsonify, Response, g
from flask_cors import CORS
from loguru import logger
from src.utility import save_temp_audio, cleanup_temp_file, validate_and_decode_base64_audio, encode_audio_base64
from src.requestID import reqID
from src.voiceMap import VOICE_BASE64_MAP
from src.server import run_audio_pipeline
from src.model_client import cleanup_model_client
from src.wittyMessages import WITTY_ERROR_MESSAGES, VALIDATION_ERROR_MESSAGES, get_validation_error, get_witty_error
import time
import traceback
import asyncio
import atexit
import random

app = Flask(__name__)
CORS(app)

# Register cleanup function
atexit.register(lambda: asyncio.run(cleanup_model_client()))



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
        },
        "message": "All systems operational! 🚀"
    })

@app.route("/audio", methods=["GET", "POST"])
def audio_endpoint():
    request_id = g.request_id
    if request.method == "GET":
        try:
            text = request.args.get("text")
            system = request.args.get("system")
            voice = request.args.get("voice")

            if not text:
                logger.warning(f"GET request {request_id} missing text parameter")
                return jsonify({"error": {"message": get_validation_error(), "code": 400}}), 400

            result = asyncio.run(run_audio_pipeline(
                reqID=request_id,
                text=text,
                voice=voice,
                synthesis_audio_path=None,
                clone_audio_transcript=None,
                system_instruction=system,
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
                logger.error(f"GET request {request_id} returned unexpected result type: {result}")
                return jsonify({"error": {"message": get_witty_error(), "code": 500}}), 500

        except Exception as e:
            logger.error(f"GET error for request {request_id}: {traceback.format_exc()}")
            return jsonify({"error": {"message": get_witty_error(), "code": 500}}), 500
        finally:
            cleanup_temp_file(request_id)

    elif request.method == "POST":
        try:
            data = request.get_json()
            if not data:
                logger.warning(f"POST request {request_id} missing JSON body")
                return jsonify({"error": {"message": get_validation_error(), "code": 400}}), 400

            # Extract parameters from JSON
            text = data.get("text")
            voice_b64 = data.get("voice_b64")
            voice_name = data.get("voice_name")
            speech_audio_b64 = data.get("speech_audio_b64")
            clone_audio_transcript = data.get("clone_audio_transcript")
            system_instruction = data.get("system_instruction")

            if not text:
                logger.warning(f"POST request {request_id} missing text parameter")
                return jsonify({"error": {"message": get_validation_error(), "code": 400}}), 400

            voice_path = None
            speech_audio_path = None

            # Handle voice cloning
            if voice_b64:
                try:
                    validate_and_decode_base64_audio(voice_b64)
                    voice_path = save_temp_audio(voice_b64, request_id, "clone")
                except Exception as e:
                    logger.warning(f"POST request {request_id} invalid voice_b64: {str(e)}")
                    return jsonify({"error": {"message": get_validation_error(), "code": 400}}), 400
            elif voice_name and not voice_b64:
                if voice_name in VOICE_BASE64_MAP:
                    coded = encode_audio_base64(VOICE_BASE64_MAP[voice_name])
                    voice_path = save_temp_audio(coded, request_id, "clone")
                else:
                    logger.warning(f"POST request {request_id} unknown voice name: {voice_name}")
                    return jsonify({"error": {"message": get_validation_error(), "code": 400}}), 400
            else:
                coded = encode_audio_base64(VOICE_BASE64_MAP.get("alloy"))
                voice_path = save_temp_audio(coded, request_id, "clone")

            # Handle speech input
            if speech_audio_b64:
                try:
                    validate_and_decode_base64_audio(speech_audio_b64)
                    speech_audio_path = save_temp_audio(speech_audio_b64, request_id, "speech")
                except Exception as e:
                    logger.warning(f"POST request {request_id} invalid speech_audio_b64: {str(e)}")
                    return jsonify({"error": {"message": get_validation_error(), "code": 400}}), 400

            result = asyncio.run(run_audio_pipeline(
                reqID=request_id,
                text=text,
                voice=voice_path,
                synthesis_audio_path=speech_audio_path,
                clone_audio_transcript=clone_audio_transcript,
                system_instruction=system_instruction,
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
                logger.error(f"POST request {request_id} returned unexpected result type: {result}")
                return jsonify({"error": {"message": get_witty_error(), "code": 500}}), 500

        except Exception as e:
            logger.error(f"POST error for request {request_id}: {traceback.format_exc()}")
            return jsonify({"error": {"message": get_witty_error(), "code": 500}}), 500
        finally:
            cleanup_temp_file(request_id)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "alive", "message": "Still breathing! 💨"}), 200

@app.errorhandler(400)
def bad_request(e):
    logger.warning(f"400 error: {str(e)}")
    return jsonify({"error": {"message": get_validation_error(), "code": 400}}), 400

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Unhandled 500 exception: {traceback.format_exc()}")
    return jsonify({"error": {"message": get_witty_error(), "code": 500}}), 500

@app.errorhandler(404)
def not_found(e):
    logger.info(f"404 error: {request.url}")
    return jsonify({"error": {"message": "This endpoint went on vacation and forgot to leave a forwarding address! 🏖️", "code": 404}}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    logger.info(f"405 error: {request.method} on {request.url}")
    return jsonify({"error": {"message": "That HTTP method is not invited to this party! Try a different one! 🎉", "code": 405}}), 405