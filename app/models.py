from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from .database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"
    id = Column(Integer, primary_key=True, index=True)
    basic_info = Column(Text, nullable=False)
    schedule_text = Column(Text, nullable=False)
    hr_zones = Column(Text, nullable=True)
    other_info = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WorkoutFile(Base):
    __tablename__ = "workout_files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    summary_text = Column(Text, nullable=True)
    plan_text = Column(Text, nullable=True)
    plan_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
