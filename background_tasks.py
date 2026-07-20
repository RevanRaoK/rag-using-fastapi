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
            print(f"[BACKGROUND TASK] Starting processing for file_id {self.file_id} (text length: {len(text)})")
            if not text or not text.strip():
                print(f"[BACKGROUND TASK] Warning: file_id {self.file_id} has empty text.")
                return

            sentences = sent_tokenize(text)
            chunks = [' '.join(sentences[i:i + self.chunk_size])
                      for i in range(0, len(sentences), self.chunk_size)]

            print(f"[BACKGROUND TASK] Created {len(chunks)} chunks for file_id {self.file_id}")

            count = 0
            for chunk in chunks:
                if not chunk.strip():
                    continue
                try:
                    response = client.embeddings.create(
                        input=chunk,
                        model='text-embedding-3-small'
                    )
                    embeddings = response.data[0].embedding

                    file_chunk = FileChunk(
                        file_id=self.file_id,
                        chunk_text=chunk,
                        embedding_vector=embeddings
                    )
                    db.add(file_chunk)
                    count += 1
                except Exception as chunk_err:
                    print(f"[BACKGROUND TASK] Error embedding chunk for file_id {self.file_id}: {chunk_err}")

            db.commit()
            print(f"[BACKGROUND TASK] Successfully saved {count} chunks for file_id {self.file_id}")
        except Exception as e:
            db.rollback()
            print(f"[BACKGROUND TASK] Critical error in chunk_and_embed for file_id {self.file_id}: {e}")
        finally:
            db.close()
