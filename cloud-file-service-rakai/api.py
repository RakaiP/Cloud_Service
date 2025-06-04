from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunk_num: int = Form(...),
    filename: str = Form(...)
):
    chunk_dir = os.path.join(UPLOAD_DIR, filename)
    os.makedirs(chunk_dir, exist_ok=True)

    chunk_path = os.path.join(chunk_dir, f"{chunk_num:05d}")
    with open(chunk_path, "wb") as f:
        f.write(await chunk.read())
    return {"status": "success"}
