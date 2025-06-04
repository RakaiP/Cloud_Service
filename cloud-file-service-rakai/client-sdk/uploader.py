import requests
from tqdm import tqdm
from .chunker import split_file

def upload_file(file_path, upload_url, chunk_size=1024*1024):
    total_size = os.path.getsize(file_path)
    num_chunks = (total_size // chunk_size) + 1

    for chunk_num, chunk in tqdm(split_file(file_path, chunk_size), total=num_chunks, desc="Uploading"):
        response = requests.post(
            upload_url,
            files={'file': chunk},
            data={'chunk_num': chunk_num}
        )
        response.raise_for_status()
        print(f"Uploaded chunk {chunk_num + 1}/{num_chunks}")