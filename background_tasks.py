from urllib.request import OpenerDirector
from sqlalchemy.orm import Session
from db import FileChunk
import nltk
from nltk.tokenize import sent_tokenize
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENAI_API_KEY,
)

nltk.download('punkt')

class TextProcessor:
  def __init__(self, db: Session, file_id: int, chunk_size: int = 2):
    self.db = db
    self.file_id = file_id
    self.chunk_size = chunk_size

  def chunk_and_embed(self, text: str):
    # Split text into sentences
    sentences = sent_tokenize(text)

    # Chunk sentences
    chunks = [' '.join(sentences[i:i + self.chunk_size])
                  for i in range(0, len(sentences), self.chunk_size)]

    for chunk in chunks:
      # Create embeddings
      response = client.embeddings.create(
        input = chunk,
        model = 'perplexity/pplx-embed-v1-4b'
      )

      embeddings = response.data[0].embedding

      # Store chunk and embedding in database
      file_chunk = FileChunk(file_id=self.file_id,
                            chunk_text=chunk,
                            embedding_vector=embeddings)
      self.db.add(file_chunk)
    
    self.db.commit()