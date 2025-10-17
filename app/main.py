import os
from typing import List
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .database import Base, engine, get_db, run_light_migrations
from .models import UserProfile, WorkoutFile, AnalysisResult
from .schemas import ProfileIn
from .fit_processing import parse_fit_file
from .gemini_client import analyze_and_plan

load_dotenv()

app = FastAPI(title="AI Running Coach")

# Create tables
Base.metadata.create_all(bind=engine)
run_light_migrations()

# Static / Templates
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

# Storage for uploads
uploads_dir = os.path.join(BASE_DIR, "uploads")
os.makedirs(uploads_dir, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).order_by(UserProfile.id.desc()).first()
    return templates.TemplateResponse("index.html", {"request": request, "profile": profile})

@app.post("/profile")
async def save_profile(
    basic_info: str = Form(...),
    schedule_text: str = Form(...),
    hr_zones: str | None = Form(None),
    other_info: str | None = Form(None),
    db: Session = Depends(get_db),
):
    prof = UserProfile(
        basic_info=basic_info,
        schedule_text=schedule_text,
        hr_zones=hr_zones,
        other_info=other_info,
    )
    db.add(prof)
    db.commit()
    return RedirectResponse("/", status_code=303)

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    saved = []
    for f in files:
        dest = os.path.join(uploads_dir, f.filename)
        content = await f.read()
        with open(dest, "wb") as out:
            out.write(content)
        summary = parse_fit_file(dest)
        wf = WorkoutFile(filename=f.filename, stored_path=dest, summary=summary)
        db.add(wf)
        saved.append({"filename": f.filename, "summary": summary})
    db.commit()
    return {"uploaded": saved}

@app.get("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).order_by(UserProfile.id.desc()).first()
    files = db.query(WorkoutFile).order_by(WorkoutFile.id.desc()).all()
    summaries = [w.summary for w in files if w.summary]
    if not profile:
        return templates.TemplateResponse("message.html", {"request": request, "message": "请先填写个人信息与时间安排。"})
    result = analyze_and_plan(
        profile={
            "basic_info": profile.basic_info,
            "hr_zones": profile.hr_zones,
            "other_info": getattr(profile, "other_info", None),
        },
        schedule_text=profile.schedule_text,
        summaries=summaries,
    )
    if result.get("error"):
        return templates.TemplateResponse("message.html", {"request": request, "message": result["error"]})
    
    text = result.get("text", "")
    plan_json = result.get("plan_json")

    # The DB model's `plan_json` column is a JSON type, so pass the dict directly.
    ar = AnalysisResult(summary_text=text, plan_text=text, plan_json=plan_json)
    db.add(ar)
    db.commit()
    return templates.TemplateResponse("results.html", {"request": request, "text": text, "plan_json": plan_json})
