# Local Setup Guide

## Prerequisites

### System Requirements

- **OS**: macOS, Linux, or Windows (WSL2 recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **CPU**: Multi-core processor (4+ cores recommended)

### Software Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **Git**: Latest version
- **Ollama**: Latest version (for local LLM)
- **ffmpeg**: Latest version (for audio processing)

---

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/airhelp.git
cd airhelp
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Install System Dependencies

**macOS**:
```bash
brew install ffmpeg
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Windows**:
```bash
# Download from https://ffmpeg.org/download.html
# Add to PATH
```

#### Install Ollama

**macOS/Linux**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows**:
```bash
# Download from https://ollama.com/download
```

#### Pull LLM Model

```bash
ollama pull gemma:2b
```

#### Setup Piper TTS (Optional)

```bash
# Download Piper voices
npm run piper:setup

# Or manually:
cd ..
npm run piper:voices
```

#### Initialize Database

```bash
# The database will be automatically initialized on first run
# Or manually:
python3 -c "from app.services.lost_found_service import init_db; init_db()"
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Edit .env if needed (optional)
nano .env
```

### 4. Environment Configuration

#### Backend Environment Variables

Create `backend/.env` (optional, uses defaults if not present):

```bash
# LLM Configuration
OLLAMA_URL=http://localhost:11434
MODEL_NAME=gemma:2b

# Whisper Configuration
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu

# Database Paths (optional)
FAISS_INDEX_PATH=./data/embeddings/faiss_index
LOST_FOUND_DB_PATH=./app/data/lost_found.sqlite3

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@airhelp.com
SMTP_USE_TLS=true

# Operator Token (optional)
AIRHELP_OPERATOR_TOKEN=your-secret-token
```

#### Frontend Environment Variables

Edit `frontend/.env`:

```bash
# API Base URL
VITE_API_BASE_URL=http://localhost:8000

# Or use localStorage override (see below)
```

**Alternative**: Set API URL in browser localStorage:
```javascript
localStorage.setItem('airhelp_api_base', 'http://localhost:8000');
```

---

## Running the Application

### Start Backend

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output**:
```
🚀 AI Airport Companion API starting...
📦 Lost & Found storage (SQLite on this laptop): /path/to/lost_found.sqlite3
📡 Operational state (operator bulletins / delays): /path/to/operational_state.json
✅ RAG initialized successfully
⏰ Alert scheduler started
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Start Frontend

```bash
cd frontend

# Start development server
npm run dev
```

**Expected Output**:
```
  VITE v5.1.4  ready in 500 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: http://192.168.1.10:3000/
  ➜  press h to show help
```

### Start Ollama (if not running)

```bash
# Ollama usually starts automatically
# If not, start manually:
ollama serve
```

---

## Verification

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

**Expected**:
```json
{"status":"healthy"}
```

### 2. Check Ollama

```bash
curl http://localhost:11434/api/tags
```

**Expected**:
```json
{
  "models": [
    {
      "name": "gemma:2b",
      "modified_at": "2026-05-07T12:00:00Z",
      "size": 1600000000
    }
  ]
}
```

### 3. Test Chat API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "message": "Where is gate B12?",
    "location": "entrance",
    "language": "en"
  }'
```

### 4. Test Voice Pipeline

```bash
# Create test audio
python3 -c "from PIL import Image; img = Image.new('RGB', (800, 400), 'white'); img.save('test.jpg')"

# Test transcription
cd backend
python3 test_transcribe_endpoint.py
```

**Expected**:
```
✅ Real transcription working!
```

### 5. Open Frontend

Navigate to http://localhost:3000 in your browser.

**Expected**: Chat interface loads, you can type messages and receive responses.

---

## Common Issues

### Issue 1: Ollama Not Running

**Symptom**: Backend fails to start with "Connection refused" error.

**Solution**:
```bash
# Start Ollama
ollama serve

# Pull model if not present
ollama pull gemma:2b
```

### Issue 2: Port Already in Use

**Symptom**: "Address already in use" error.

**Solution**:
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Issue 3: faster-whisper Not Found

**Symptom**: "This is a mock transcription because Whisper is not loaded."

**Solution**:
```bash
# Install faster-whisper in virtual environment
.venv/bin/pip install faster-whisper

# Restart backend
```

### Issue 4: ChromaDB Errors

**Symptom**: "Collection not found" or "Database locked" errors.

**Solution**:
```bash
# Delete and reinitialize ChromaDB
rm -rf backend/chroma_db
rm -rf chroma_db

# Restart backend (will reinitialize)
```

### Issue 5: Frontend Can't Connect to Backend

**Symptom**: "Network error" or "Failed to fetch" in browser console.

**Solution**:
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS configuration in backend/app/main.py
# Ensure allow_origins includes frontend URL

# Or set API URL in localStorage
localStorage.setItem('airhelp_api_base', 'http://localhost:8000');
```

### Issue 6: Piper TTS Not Working

**Symptom**: TTS returns error or no audio.

**Solution**:
```bash
# Install Piper voices
npm run piper:setup

# Or download manually
cd piper
./download_voices.sh

# Check TTS status
curl http://localhost:8000/api/tts/status
```

---

## Development Workflow

### Hot Reload

Both backend and frontend support hot reload:

- **Backend**: `--reload` flag automatically reloads on code changes
- **Frontend**: Vite automatically reloads on code changes

### Debugging

#### Backend Debugging

```python
# Add breakpoints
import pdb; pdb.set_trace()

# Or use VS Code debugger
# Create .vscode/launch.json:
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

#### Frontend Debugging

```javascript
// Use browser DevTools
console.log('Debug:', data);

// Or use VS Code debugger with Chrome
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Or run specific test
python3 test_chat_flow.py

# Frontend tests (if configured)
cd frontend
npm test
```

### Logging

#### Backend Logs

```bash
# View logs in terminal
# Or configure file logging in app/utils/logger.py

# Increase log level
export LOG_LEVEL=DEBUG
```

#### Frontend Logs

```bash
# Open browser DevTools (F12)
# Check Console tab for logs
```

---

## Data Management

### Reset User Data

```bash
cd backend

# Reset user profiles
python3 manage_users.py --reset

# Or manually
rm app/data/users.json
```

### Reset Lost & Found

```bash
cd backend

# Delete database
rm app/data/lost_found.sqlite3

# Restart backend (will recreate)
```

### Reset Vector Database

```bash
# Delete ChromaDB
rm -rf backend/chroma_db
rm -rf chroma_db

# Restart backend (will reinitialize)
```

### Update Airport Data

```bash
cd backend

# Update facilities
python3 scripts/generate_csmia_facilities_csv.py

# Update shops
python3 scripts/generate_csmia_shop_csv.py

# Rebuild graph
python3 scripts/build_mumbai_t2_l02_graph.py

# Restart backend
```

---

## Performance Optimization

### Backend Optimization

```bash
# Use production ASGI server
pip install gunicorn

# Run with multiple workers
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend Optimization

```bash
# Build for production
npm run build

# Serve with static server
npm install -g serve
serve -s dist -p 3000
```

### Database Optimization

```bash
# Optimize ChromaDB
# (Automatic, no action needed)

# Optimize SQLite
sqlite3 app/data/lost_found.sqlite3 "VACUUM;"
```

---

## Next Steps

After successful setup:

1. **Explore the UI**: Try different queries in the chat interface
2. **Test Voice Input**: Click the microphone button and speak
3. **Test Navigation**: Ask for directions between locations
4. **Review Logs**: Check backend logs for any warnings
5. **Read Documentation**: Explore architecture and API docs

---

## Quick Reference

### Start Everything

```bash
# Terminal 1: Backend
cd backend && source .venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Ollama (if needed)
ollama serve
```

### Stop Everything

```bash
# Press Ctrl+C in each terminal
```

### Restart Everything

```bash
# Stop all (Ctrl+C)
# Then start again (see above)
```

---

**Related Documentation**:
- [Environment Variables](environment-variables.md)
- [Docker Setup](docker-setup.md)
- [Troubleshooting](troubleshooting.md)
