async function upload() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a file to upload.');
        return;
    }

    const progressBar = document.getElementById('progressBar');
    progressBar.value = 0;

    // Using the block-storage service endpoint
    const UPLOAD_URL = 'http://localhost:8003';
    const chunkSize = 1024 * 1024; // 1MB chunks
    const totalChunks = Math.ceil(file.size / chunkSize);

    try {
        // Initialize upload
        const initResponse = await fetch(`${UPLOAD_URL}/upload/init`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                filename: file.name,
                total_size: file.size
            })
        });

        if (!initResponse.ok) {
            throw new Error('Failed to initialize upload');
        }

        const { upload_id } = await initResponse.json();

        // Upload chunks
        for (let i = 0; i < totalChunks; i++) {
            const start = i * chunkSize;
            const end = Math.min(start + chunkSize, file.size);
            const chunk = file.slice(start, end);

            const formData = new FormData();
            formData.append('file', chunk);
            formData.append('upload_id', upload_id);
            formData.append('chunk_number', i.toString());

            const response = await fetch(`${UPLOAD_URL}/upload/chunk`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Failed to upload chunk ${i}`);
            }

            progressBar.value = ((i + 1) / totalChunks) * 100;
        }

        // Complete upload
        const completeResponse = await fetch(`${UPLOAD_URL}/upload/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                upload_id: upload_id
            })
        });

        if (!completeResponse.ok) {
            throw new Error('Failed to complete upload');
        }

        alert('File uploaded successfully!');
        progressBar.value = 0;
    } catch (error) {
        console.error('Error:', error);
        alert(`Upload failed: ${error.message}`);
    }
}
