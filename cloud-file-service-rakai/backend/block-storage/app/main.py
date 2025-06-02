from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chunks import router as chunks_router
import os

app = FastAPI(
    title="Block Storage Service API",
    version="1.0.0",
    description="API for storing, retrieving, and deleting file chunks."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure storage directory exists
os.makedirs("storage", exist_ok=True)

app.include_router(chunks_router, prefix="/chunks", tags=["chunks"])

@app.get("/")
async def root():
    return {"status": "Block Storage Service is running", "service": "block-storage"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "block-storage"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
