cd ~/audio.pollinations || { echo "Directory not found"; exit 1; }

# Clear port 8000 if in use
echo "Checking if port 8000 is in use and clearing it..."
sudo lsof -ti:8000 | xargs -r sudo kill -9

# Create virtual environment if not exists
if [ ! -d "higgs_audio_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv higgs_audio_env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source higgs_audio_env/bin/activate

# Upgrade pip and install dependencies
echo "Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Start the app with flask
echo "Starting the app on port 8000..."
python3 src/app.py &
