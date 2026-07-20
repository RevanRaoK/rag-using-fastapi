from fastapi import FastAPI, UploadFile, HTTPException
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import shutil
import io

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


@app.get("/")
def root():
  return "Hello RAG fellow!"

@app.post("/uploadfile/")
async def upload_file(file: UploadFile):
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

    return {"info": "File saved!", 'Filename': "file.filename"}
  except Exception as e:
    # Log the exception
    print("Error saving file: {e}")
    raise HTTPException(status_code=500, detail='Error saving file')

@app.post("/ask/")
async def ask_question(question: Question):
  if not OPENAI_API_KEY:
    raise HTTPException(status_code=500, detail="OpenAI API key not configured")
  try:
    response = client.chat.completions.create(
      model='inclusionai/ling-2.6-flash',
      messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question.question}
      ]
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
  return {"response": response.choices[0].message.content}