from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from ..services.block_storage_client import BlockStorageClient, FileChunker
from ..models.file import FileChunk
import uuid
from sqlalchemy.orm import Session
from ..dependencies import get_db, get_current_user
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Upload a file with automatic chunking and storage"""
    try:
        # Read file data
        file_data = await file.read()
        file_id = str(uuid.uuid4())
        
        # Initialize services
        block_client = BlockStorageClient()
        chunker = FileChunker()
        
        # Create file record
        db_file = File(
            id=file_id,
            filename=file.filename,
            size=len(file_data),
            content_type=file.content_type,
            owner_id=current_user["sub"],
            upload_status="uploading"
        )
        db.add(db_file)
        db.commit()
        
        # Chunk the file
        chunks = chunker.chunk_file(file_data, file_id)
        db_file.total_chunks = len(chunks)
        
        uploaded_chunks = []
        
        # Upload each chunk
        for chunk_info in chunks:
            try:
                # Upload to block storage
                upload_result = block_client.upload_chunk(
                    chunk_info["data"], 
                    chunk_info["chunk_id"]
                )
                
                # Save chunk metadata
                db_chunk = FileChunk(
                    file_id=file_id,
                    chunk_id=chunk_info["chunk_id"],
                    chunk_index=chunk_info["chunk_index"],
                    size=chunk_info["size"],
                    hash=chunk_info["hash"]
                )
                db.add(db_chunk)
                uploaded_chunks.append(chunk_info["chunk_id"])
                
            except Exception as e:
                # Cleanup on failure
                for cleanup_chunk_id in uploaded_chunks:
                    try:
                        block_client.delete_chunk(cleanup_chunk_id)
                    except:
                        pass
                
                db.delete(db_file)
                db.commit()
                raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
        
        # Mark upload as completed
        db_file.upload_status = "completed"
        db.commit()
        
        return {
            "message": "File uploaded successfully",
            "file_id": file_id,
            "filename": file.filename,
            "size": len(file_data),
            "chunks": len(chunks),
            "upload_status": "completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Download a file by reconstructing from chunks"""
    # Get file record
    db_file = db.query(File).filter(File.id == file_id).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check ownership or permissions
    if db_file.owner_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Get all chunks ordered by index
        chunks = db.query(FileChunk).filter(
            FileChunk.file_id == file_id
        ).order_by(FileChunk.chunk_index).all()
        
        if len(chunks) != db_file.total_chunks:
            raise HTTPException(status_code=500, detail="File incomplete - missing chunks")
        
        # Download and reconstruct file
        block_client = BlockStorageClient()
        chunker = FileChunker()
        chunk_data_list = []
        
        for chunk in chunks:
            chunk_data = block_client.download_chunk(chunk.chunk_id)
            chunk_data_list.append(chunk_data)
        
        # Reconstruct file
        file_data = chunker.reconstruct_file(chunk_data_list)
        
        return StreamingResponse(
            BytesIO(file_data),
            media_type=db_file.content_type or "application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={db_file.filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")