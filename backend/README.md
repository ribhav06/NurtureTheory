# Pēds Backend — FastAPI

A Python FastAPI backend for the Pēds pediatric co-pilot app.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

4. Run the server:
```bash
uvicorn main:app --reload --port 8000
```
