from fastapi import (FastAPI, UploadFile, HTTPException, Depends, BackgroundTasks)
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import shutil
import io
from db import get_db, File, FileChunk
from sqlalchemy.orm import Session
from file_parser import FileParser
from background_tasks import TextProcessor, client
from sqlalchemy import select

app = FastAPI()

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client with OpenRouter's base URL and your key
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPENAI_API_KEY,
)

class Question(BaseModel):
  question: str

class AskModel(BaseModel):
  document_id: int
  question: str

class QuestionModel(BaseModel):
  question: str


@app.get("/")
def root():
  return "Hello RAG fellow!"

@app.post("/uploadfile/")
async def upload_file(file: UploadFile, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
  # define allowed extensions
  allowed_extensions = ['txt', 'pdf']

  # check if the fine extension is allowed
  file_extension = file.filename.split('.')[-1]
  if file_extension not in allowed_extensions:
    raise HTTPException(status_code=400, detail="File type is not allowed")

  # Define the sources folder
  folder = 'sources'
  try:
    # ensure the directory exists
    os.makedirs(folder, exist_ok=True)

    # Secure way to save the files
    file_location = os.path.join(folder, file.filename)
    file_content = await file.read() # reads file content as bytes
    with open(file_location, "wb+") as file_object:
      # convert bytes content to a file-like object
      file_like_object = io.BytesIO(file_content)
      # use shutil.copyfileobj for secure file writing
      shutil.copyfileobj(file_like_object, file_object)

    # Parse file text content
    parser = FileParser(filepath=file_location)
    parsed_text = parser.parse()

    # Save file record to database
    db_file = File(file_name=file.filename, file_content=parsed_text)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Trigger background chunking and embedding
    processor = TextProcessor(file_id=db_file.file_id)
    background_tasks.add_task(processor.chunk_and_embed, parsed_text)

    return {"info": "File saved and processing started!", "file_id": db_file.file_id, "filename": file.filename}
  except Exception as e:
    # Log the exception
    print(f"Error saving file: {e}")
    raise HTTPException(status_code=500, detail=f"Error saving file: {e}")

# Function to get similar chunks
async def get_similar_chunks(file_id: int, question: str, db: Session):
  try:
    # Create embeddings for the question (assuming client and embedding creation logic)
    response = client.embeddings.create(input=question, model='perplexity/pplx-embed-v1-4b')
    question_embedding = response.data[0].embedding

    similar_chunks_query = (
      select(FileChunk)
      .where(FileChunk.file_id == file_id)
      .order_by(FileChunk.embedding_vector.l2_distance(question_embedding))
      .limit(10)
    )
    similar_chunks = db.scalars(similar_chunks_query).all()

    return similar_chunks
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/")
async def ask_question(request: AskModel, db: Session = Depends(get_db)):
  if OPENAI_API_KEY is None:
    raise HTTPException(status_code=500, detail="OpenAI API key not set")

  try:
    similar_chunks = await get_similar_chunks(request.document_id, request.question, db)

    # construct context from similar chunks' text
    context_texts = [chunk.chunk_text for chunk in similar_chunks]
    context = " ".join(context_texts)

    # update the system message with the context
    # update the system message with the context
    system_message = (
        "You are an expert AI assistant answering questions about an uploaded document. "
        "Use ONLY the following extracted context to answer the question. "
        "If the context does not contain enough information to answer, state clearly "
        "what information is available or that the context does not specify it.\n\n"
        f"Context:\n{context}"
    )

    # Make the OpenAI API  call with the updated context
    response = client.chat.completions.create(
      model='inclusionai/ling-2.6-flash',
      messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": request.question},
      ]
    )

    return {"response": response.choices[0].message.content}
  
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

@app.post("/find-similar-chunks/{file_id}")
async def find_similar_chunks_endpoint(file_id: int, question_data: QuestionModel, db: Session = Depends(get_db)):
  try:
    similar_chunks = await get_similar_chunks(file_id, question_data.question, db)

    # Format response
    formatted_response = [
      {"chunk_id": chunk.chunk_id, "chunk_text": chunk.chunk_text}
      for chunk in similar_chunks
    ]

    return formatted_response
  
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))