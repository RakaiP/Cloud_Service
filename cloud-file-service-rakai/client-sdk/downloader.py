import requests
from .chunker import reconstruct_file

def download_chunks(base_url, num_chunks):
    chunks = []
    for i in tqdm(range(num_chunks), desc="Downloading"):
        response = requests.get(f"{base_url}?chunk_num={i}")
        response.raise_for_status()
        chunks.append((i, response.content))
    return chunks

def download_file(base_url, num_chunks, output_path):
    chunks = download_chunks(base_url, num_chunks)
    reconstruct_file(chunks, output_path)
