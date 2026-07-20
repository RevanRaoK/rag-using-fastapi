from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import text
from sqlalchemy_utils import database_exists, create_database
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv
import urllib
import os

load_dotenv()

# Database Credentials & URL
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
  # Cloud providers (like Railway/Render/Heroku) often use postgres:// instead of postgresql://
  if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
  database_url = DATABASE_URL
else:
  POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME", "postgres")
  POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mysecretpassword")
  POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
  POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
  DATABASE_NAME = os.getenv("DATABASE_NAME", "rag_db")
  
  encoded_password = urllib.parse.quote_plus(POSTGRES_PASSWORD)
  database_url = f"postgresql://{POSTGRES_USERNAME}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"

# Create the engine for the specific database
engine = create_engine(database_url)

# Check and create the database
try:
  if not database_exists(engine.url):
    create_database(engine.url)
    print("Database created successfully")
except Exception as e:
  print(f"Database exist check skipped: {e}")

# Session local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()

# define models
Base = declarative_base()

class File(Base):
  __tablename__ = 'files'
  file_id = Column(Integer, primary_key=True)
  file_name = Column(String(255))
  file_content = Column(Text)
  
class FileChunk(Base):
  __tablename__ = 'file-chunks'
  chunk_id = Column(Integer, primary_key=True)
  file_id = Column(Integer, ForeignKey('files.file_id'))
  chunk_text = Column(Text)
  embedding_vector = Column(Vector(2560))

# Safe database initialization
try:
  with engine.begin() as connection:
    connection.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    # Alter column dimension if table already exists with old 1536 dimension
    connection.execute(text('ALTER TABLE "file-chunks" ALTER COLUMN embedding_vector TYPE vector(2560)'))
  Base.metadata.create_all(engine)
  print("Database tables initialized successfully")
except Exception as e:
  print(f"Warning: Database initialization info: {e}")