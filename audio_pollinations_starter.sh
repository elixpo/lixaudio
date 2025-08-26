cd ~/scratch/audio.pollinations || { echo "Directory not found"; exit 1; }

sudo lsof -ti:8000 | xargs -r sudo kill -9
sudo lsof -ti:8001 | xargs -r sudo kill -9
# ./cleanup.sh
if [ ! -d "higgs_audio_env" ]; then
    python3 -m venv higgs_audio_env
fi

source higgs_audio_env/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

cleanup() {
    if [ ! -z "$MODEL_SERVER_PID" ]; then
        kill $MODEL_SERVER_PID 2>/dev/null
    fi
    if [ ! -z "$FLASK_APP_PID" ]; then
        kill $FLASK_APP_PID 2>/dev/null
    fi
    exit
}

trap cleanup EXIT INT TERM

python -m uvicorn src.model_server:app --host 0.0.0.0 --port 8001 --workers 1 &
MODEL_SERVER_PID=$!

sleep 15

if ! kill -0 $MODEL_SERVER_PID 2>/dev/null; then
    exit 1
fi

for i in {1..10}; do
    if curl -s http://localhost:8001/health > /dev/null; then
        break
    fi
    if [ $i -eq 10 ]; then
        exit 1
    fi
    sleep 3
done

gunicorn -w 15 -b 0.0.0.0:8000 --worker-class gevent --worker-connections 1000 src.app:app &
FLASK_APP_PID=$!

sleep 5

echo "Services started successfully!"
echo "- Model server: http://localhost:8001 (PID: $MODEL_SERVER_PID)"
echo "- Flask app: http://localhost:8000 (PID: $FLASK_APP_PID)"
echo "Press Ctrl+C to stop all services"

wait
