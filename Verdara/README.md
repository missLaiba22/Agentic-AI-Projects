# Verdara

An agentic AI-powered debate platform where multiple AI agents discuss topics from different perspectives and reach verdicts.

## Features

- **Multi-Agent Debate**: Pro, Con, Judge, and Research agents collaborate to analyze topics
- **Real-time Responses**: Built with LangGraph for orchestrated agent interactions
- **REST API**: FastAPI backend for debate sessions
- **React Frontend**: Clean UI for viewing debate proceedings and verdicts

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- LangGraph
- LangChain

**Frontend:**
- React + TypeScript
- Vite
- Axios

## Setup

### Prerequisites
- Python 3.10+
- Node.js 16+

### Backend
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate  # Windows
pip install -r ../requirements.txt
python -m uvicorn routes:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

The backend runs on `http://localhost:8000` and frontend on `http://localhost:5173`.

## Usage

1. Start the backend server
2. Start the frontend dev server
3. Visit the app and initiate a debate session
4. Agents will discuss and provide a verdict

## Project Structure

```
backend/       # FastAPI server and agent logic
frontend/      # React application
agents/        # AI agent implementations
services/      # Business logic and orchestration
schemas/       # Data models
```

## License

MIT
