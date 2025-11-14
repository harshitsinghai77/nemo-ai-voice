# Nemo Agentic Voice Planner

> **Proof-of-Concept:** Agentic voice & chat interface that helps plan Jira tasks through voice.

## What It Does

1. Conversational Voice Agent: Story planning via natural language (duplex audio/text).
2. Multimodal Transport: Uses WebRTC (audio) and WebSockets (text) for real-time conversation.
3. Contextual: Integrates with Jira, Confluence, and GitHub to read documentation and code for richer planning context.
4. Automated Workflow: Creates and populates final Jira stories automatically after planning is complete.
5. Planner Proposals (WIP): Agent proposes structured plans and ask questions to help user finalize the plan.

## Repository Layout

```
/backend   – FastAPI server, Pipecat pipeline, custom & integration tools
/frontend  – React app (Vite/C-RA)
Dockerfile – Container build for backend + frontend
```

## Key Technologies

- Python / FastAPI – REST & WebSocket backend, Pipecat orchestration
- React – Lightweight, modern UI components
- Pipecat SDK – Client & server transports, audio handling
- AWS - Bedrock, Polly, Transcribe

## Quick Start

```bash
# 1. Backend (Python 3.11+)
cp .env.example .env          # add your keys
pip install -r requirements.txt
python server.py              # starts FastAPI on :7860

# 2. Frontend
cd frontend
npm install                   # first time
npm run dev                   # React dev server
```

Open `http://localhost:5173` (or shown dev URL). The React app will connect to the backend on `:7860`.

## Required Environment Variables

| Variable | Purpose |
|----------|---------|
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | S3 / Polly / Transcribe (example) |
| `DEEPGRAM_API_KEY` | Speech-to-Text service |
| `CARTESIA_TTS_API_KEY` | Text-to-Speech voice |
| `ATLASSIAN_API_TOKEN`, `ATLASSIAN_EMAIL`, `JIRA_BASE_URL` | Jira / Confluence integration |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub cloning actions |

Create a local `.env` with these values or inject via your deployment platform.

## Running in Docker (Optional)

```bash
docker build -t nemo-agentic .
docker run -p 7860:7860 -p 5173:5173 --env-file .env nemo-agentic
```
