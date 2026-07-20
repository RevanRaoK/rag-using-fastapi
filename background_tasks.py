from urllib.request import OpenerDirector
from sqlalchemy.orm import Session
from db import FileChunk
import nltk
from nltk.tokenize import sent_tokenize
from openai import OpenAI
from dotenv import load_dotenv
import os
from db import FileChunk, SessionLocal

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENAI_API_KEY,
)

nltk.download('punkt')
nltk.download('punkt_tab')

class TextProcessor:
    def __init__(self, file_id: int, chunk_size: int = 2):
        self.file_id = file_id
        self.chunk_size = chunk_size

    def chunk_and_embed(self, text: str):
        db = SessionLocal()
        try:
            sentences = sent_tokenize(text)
            chunks = [' '.join(sentences[i:i + self.chunk_size])
                      for i in range(0, len(sentences), self.chunk_size)]

            for chunk in chunks:
                response = client.embeddings.create(
                    input=chunk,
                    model='perplexity/pplx-embed-v1-4b'
                )
                embeddings = response.data[0].embedding

                file_chunk = FileChunk(
                    file_id=self.file_id,
                    chunk_text=chunk,
                    embedding_vector=embeddings
                )
                db.add(file_chunk)
            
            db.commit()
        finally:
            db.close()
