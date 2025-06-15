from minio import Minio
from minio.error import S3Error
import os
import time

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin123")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "chunks")

print(f"MinIO Config - Endpoint: {MINIO_ENDPOINT}, Bucket: {MINIO_BUCKET}")

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,  # Set to True for HTTPS
)

def wait_for_minio(max_retries=10, delay=2):
    """Wait for MinIO to be available"""
    for i in range(max_retries):
        try:
            minio_client.list_buckets()
            print("MinIO is available!")
            return True
        except Exception as e:
            print(f"Waiting for MinIO... (attempt {i+1}/{max_retries}): {e}")
            time.sleep(delay)
    return False

def ensure_bucket(bucket_name: str = MINIO_BUCKET):
    """Create bucket if it doesn't exist"""
    try:
        # Wait for MinIO to be available
        if not wait_for_minio():
            raise Exception("MinIO not available after waiting")
            
        found = minio_client.bucket_exists(bucket_name)
        if not found:
            minio_client.make_bucket(bucket_name)
            print(f"Created bucket '{bucket_name}'")
        else:
            print(f"Bucket '{bucket_name}' already exists")
    except S3Error as exc:
        print(f"MinIO S3 error occurred: {exc}")
        raise
    except Exception as exc:
        print(f"Error occurred: {exc}")
        raise

def upload_chunk(chunk_id: str, data: bytes, bucket_name: str = MINIO_BUCKET):
    """Upload chunk to MinIO"""
    from io import BytesIO
    try:
        print(f"Uploading {len(data)} bytes to bucket '{bucket_name}' with key '{chunk_id}'")
        minio_client.put_object(
            bucket_name,
            chunk_id,
            BytesIO(data),
            length=len(data),
            content_type="application/octet-stream"
        )
        print(f"Successfully uploaded chunk {chunk_id}")
        return True
    except S3Error as exc:
        print(f"Error uploading chunk {chunk_id}: {exc}")
        raise
    except Exception as exc:
        print(f"Unexpected error uploading chunk {chunk_id}: {exc}")
        raise

def download_chunk(chunk_id: str, bucket_name: str = MINIO_BUCKET):
    """Download chunk from MinIO with performance monitoring"""
    import time
    try:
        start_time = time.time()
        
        response = minio_client.get_object(bucket_name, chunk_id)
        data = response.read()
        
        end_time = time.time()
        download_time = end_time - start_time
        
        # 📊 PERFORMANCE MONITORING: Log slow MinIO operations
        if download_time > 1.0:
            print(f"🐌 Slow MinIO download: {chunk_id} took {download_time:.2f}s for {len(data)} bytes")
        
        return data
        
    except S3Error as exc:
        print(f"Error downloading chunk {chunk_id}: {exc}")
        raise

def delete_chunk(chunk_id: str, bucket_name: str = MINIO_BUCKET):
    """Delete chunk from MinIO"""
    try:
        minio_client.remove_object(bucket_name, chunk_id)
        return True
    except S3Error as exc:
        print(f"Error deleting chunk {chunk_id}: {exc}")
        raise

def list_chunks(bucket_name: str = MINIO_BUCKET):
    """List all chunks in bucket"""
    try:
        objects = minio_client.list_objects(bucket_name)
        return [obj.object_name for obj in objects]
    except S3Error as exc:
        print(f"Error listing chunks: {exc}")
        raise
