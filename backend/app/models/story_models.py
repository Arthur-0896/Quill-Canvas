from sqlalchemy import Column, String, Text, DateTime, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class StoryStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class SceneStatus(str, enum.Enum):
    DETECTED = "detected"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Story(Base):
    __tablename__ = "stories"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=True)  # For multi-user support
    title = Column(String(255), nullable=True)
    content = Column(Text)
    status = Column(Enum(StoryStatus), default=StoryStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Scene(Base):
    __tablename__ = "scenes"
    
    id = Column(String, primary_key=True)
    story_id = Column(String, nullable=False)
    sequence = Column(Integer)  # Order in story
    title = Column(String(255))
    description = Column(Text)
    image_prompt = Column(Text)
    image_url = Column(String(500), nullable=True)
    status = Column(Enum(SceneStatus), default=SceneStatus.DETECTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
