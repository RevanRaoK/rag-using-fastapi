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

# Database Credentials
POSTGRES_USERNAME = os.getenv("POSTGRES_USERNAME")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
encoded_password = urllib.parse.quote_plus(POSTGRES_PASSWORD)

# Create the engine for the specific database
database_url = f"postgresql://{POSTGRES_USERNAME}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{DATABASE_NAME}"
engine = create_engine(database_url)

# Check and create the database
if not database_exists(engine.url):
  create_database(engine.url)
  print("Database created successfully")

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
  embedding_vector = Column(Vector(1536))

# Ensure the vector extension is enabled
with engine.begin() as connection:
  connection.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

try:
  # Create tables
  Base.metadata.create_all(engine)
except Exception as e:
  print(f"Error creating tables: {e}")