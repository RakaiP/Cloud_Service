def split_file(file_path, chunk_size):
    with open(file_path, 'rb') as f:
        chunk_num = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk_num, chunk
            chunk_num += 1

def reconstruct_file(chunks, output_path):
    with open(output_path, 'wb') as f:
        for _, chunk in sorted(chunks):
            f.write(chunk)
