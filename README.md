# AI Running Coach (FastAPI)

## Setup

1. Create and fill `.env` from `.env.example`:

```
GEMINI_API_KEY=your_key_here
DATABASE_URL=sqlite:///./data/app.db
```

2. Install dependencies (recommend venv):

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

3. Run server:

```
uvicorn app.main:app --reload --port 8000
```

4. Open http://localhost:8000

## Notes
- Upload `.fit` files; they are parsed via `fitparse` to extract distance, duration, and heart rate summary.
- Profile and schedule are stored locally in SQLite. The plan generation keeps your weekly structure unless there is an obvious issue.
- Gemini API is used for analysis and plan text generation. Ensure `GEMINI_API_KEY` is set.
