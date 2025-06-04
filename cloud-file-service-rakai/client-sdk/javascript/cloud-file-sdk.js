/**
 * Cloud File Service SDK for JavaScript/Node.js
 * 
 * Based on tested backend architecture:
 * - Block Storage Service (Port 8003): Chunk upload/download
 * - Metadata Service (Port 8000): File metadata with Auth0
 */

class CloudFileClient {
    constructor(config) {
        this.metadataServiceUrl = config.metadataServiceUrl || 'http://localhost:8000';
        this.blockStorageUrl = config.blockStorageUrl || 'http://localhost:8003';
        this.auth0Domain = config.auth0Domain;
        this.apiAudience = config.apiAudience;
        this.chunkSize = config.chunkSize || 1024 * 1024; // 1MB chunks (tested optimal size)
        this.token = config.token; // Optional: provide token directly
        this.maxRetries = config.maxRetries || 3;
    }

    /**
     * Set authentication token (from Auth0 or manual)
     */
    setToken(token) {
        this.token = token;
    }

    /**
     * Get authentication headers for metadata service
     */
    getAuthHeaders() {
        if (!this.token) {
            throw new Error('No authentication token set. Call setToken() first.');
        }
        return {
            'Authorization': `Bearer ${this.token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Upload a file using the tested chunking strategy
     */
    async uploadFile(filePath, options = {}) {
        const fs = require('fs');
        const path = require('path');
        
        try {
            // Read file
            const fileBuffer = fs.readFileSync(filePath);
            const fileName = options.fileName || path.basename(filePath);
            
            console.log(`Uploading file: ${fileName} (${fileBuffer.length} bytes)`);
            
            // Step 1: Create file metadata (tested: returns 201 Created)
            const fileMetadata = await this.createFileMetadata(fileName, fileBuffer.length);
            console.log(`Created file metadata: ${fileMetadata.file_id}`);
            
            // Step 2: Split file into chunks
            const chunks = this.splitFileIntoChunks(fileBuffer);
            console.log(`Split into ${chunks.length} chunks`);
            
            // Step 3: Upload chunks to block storage (tested: fast upload)
            const chunkPromises = chunks.map((chunk, index) => 
                this.uploadChunk(fileMetadata.file_id, chunk, index, options.onProgress)
            );
            
            const chunkResults = await Promise.all(chunkPromises);
            console.log(`Uploaded ${chunkResults.length} chunks successfully`);
            
            // Step 4: Register chunks in metadata service
            for (let i = 0; i < chunkResults.length; i++) {
                await this.registerChunk(fileMetadata.file_id, chunkResults[i].chunk_id, i);
            }
            
            console.log(`File upload completed: ${fileMetadata.file_id}`);
            return {
                fileId: fileMetadata.file_id,
                fileName: fileName,
                size: fileBuffer.length,
                chunks: chunkResults.length
            };
            
        } catch (error) {
            console.error('Upload failed:', error);
            throw error;
        }
    }

    /**
     * Create file metadata using tested endpoint
     */
    async createFileMetadata(fileName, size) {
        const response = await fetch(`${this.metadataServiceUrl}/files`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                filename: fileName,
                size: size
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to create file metadata: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    /**
     * Split file into chunks (based on tested optimal size)
     */
    splitFileIntoChunks(fileBuffer) {
        const chunks = [];
        for (let i = 0; i < fileBuffer.length; i += this.chunkSize) {
            chunks.push(fileBuffer.slice(i, i + this.chunkSize));
        }
        return chunks;
    }

    /**
     * Upload chunk to block storage (tested endpoint)
     */
    async uploadChunk(fileId, chunkBuffer, chunkIndex, onProgress) {
        const chunkId = `${fileId}-chunk-${chunkIndex}`;
        
        // Create FormData for multipart upload (tested format)
        const formData = new FormData();
        const blob = new Blob([chunkBuffer]);
        formData.append('file', blob, `chunk-${chunkIndex}`);
        formData.append('chunk_id', chunkId);

        let attempt = 0;
        while (attempt < this.maxRetries) {
            try {
                const response = await fetch(`${this.blockStorageUrl}/chunks`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`Chunk upload failed: ${response.status}`);
                }

                const result = await response.json();
                
                if (onProgress) {
                    onProgress({
                        chunkIndex,
                        totalChunks: null, // Will be set by caller
                        chunkSize: chunkBuffer.length
                    });
                }
                
                return {
                    chunk_id: chunkId,
                    size: chunkBuffer.length,
                    index: chunkIndex
                };
                
            } catch (error) {
                attempt++;
                if (attempt >= this.maxRetries) {
                    throw new Error(`Chunk ${chunkIndex} upload failed after ${this.maxRetries} attempts: ${error.message}`);
                }
                console.warn(`Chunk ${chunkIndex} upload attempt ${attempt} failed, retrying...`);
                await this.delay(1000 * attempt); // Exponential backoff
            }
        }
    }

    /**
     * Register chunk in metadata service
     */
    async registerChunk(fileId, chunkId, chunkIndex) {
        const response = await fetch(`${this.metadataServiceUrl}/files/${fileId}/chunks`, {
            method: 'POST',
            headers: this.getAuthHeaders(),
            body: JSON.stringify({
                chunk_index: chunkIndex,
                storage_path: chunkId
            })
        });

        if (!response.ok) {
            console.warn(`Failed to register chunk ${chunkIndex} for file ${fileId}`);
            // Non-fatal error - chunk is uploaded, just not tracked
        }

        return await response.json();
    }

    /**
     * Download file by reconstructing chunks
     */
    async downloadFile(fileId, outputPath = null) {
        try {
            console.log(`Downloading file: ${fileId}`);
            
            // Get file metadata
            const fileInfo = await this.getFileInfo(fileId);
            console.log(`File info: ${fileInfo.filename} (${fileInfo.chunks || 'unknown'} chunks)`);
            
            // Get chunk list
            const chunks = await this.getFileChunks(fileId);
            console.log(`Found ${chunks.length} chunks`);
            
            // Download all chunks
            const chunkPromises = chunks.map(chunk => 
                this.downloadChunk(chunk.storage_path)
            );
            
            const chunkBuffers = await Promise.all(chunkPromises);
            
            // Reconstruct file
            const fileBuffer = Buffer.concat(chunkBuffers);
            
            if (outputPath) {
                const fs = require('fs');
                fs.writeFileSync(outputPath, fileBuffer);
                console.log(`File downloaded to: ${outputPath}`);
            }
            
            return fileBuffer;
            
        } catch (error) {
            console.error('Download failed:', error);
            throw error;
        }
    }

    /**
     * Get file information from metadata service
     */
    async getFileInfo(fileId) {
        const response = await fetch(`${this.metadataServiceUrl}/files/${fileId}`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) {
            throw new Error(`Failed to get file info: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Get file chunks from metadata service
     */
    async getFileChunks(fileId) {
        const response = await fetch(`${this.metadataServiceUrl}/files/${fileId}/chunks`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) {
            throw new Error(`Failed to get file chunks: ${response.status}`);
        }

        const chunks = await response.json();
        return chunks.sort((a, b) => a.chunk_index - b.chunk_index);
    }

    /**
     * Download chunk from block storage
     */
    async downloadChunk(chunkId) {
        const response = await fetch(`${this.blockStorageUrl}/chunks/${chunkId}`);

        if (!response.ok) {
            throw new Error(`Failed to download chunk ${chunkId}: ${response.status}`);
        }

        return await response.arrayBuffer();
    }

    /**
     * List user's files
     */
    async listFiles() {
        const response = await fetch(`${this.metadataServiceUrl}/files`, {
            headers: { 'Authorization': `Bearer ${this.token}` }
        });

        if (!response.ok) {
            throw new Error(`Failed to list files: ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Delete file and its chunks
     */
    async deleteFile(fileId) {
        try {
            // Get chunks first
            const chunks = await this.getFileChunks(fileId);
            
            // Delete chunks from block storage
            const deletePromises = chunks.map(chunk => 
                this.deleteChunk(chunk.storage_path)
            );
            await Promise.all(deletePromises);
            
            // Delete file metadata
            const response = await fetch(`${this.metadataServiceUrl}/files/${fileId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (!response.ok) {
                throw new Error(`Failed to delete file: ${response.status}`);
            }

            console.log(`File ${fileId} deleted successfully`);
            return true;
            
        } catch (error) {
            console.error('Delete failed:', error);
            throw error;
        }
    }

    /**
     * Delete chunk from block storage
     */
    async deleteChunk(chunkId) {
        const response = await fetch(`${this.blockStorageUrl}/chunks/${chunkId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            console.warn(`Failed to delete chunk ${chunkId}: ${response.status}`);
        }
    }

    /**
     * Utility: delay for retries
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Node.js export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CloudFileClient };
}

// Browser export  
if (typeof window !== 'undefined') {
    window.CloudFileClient = CloudFileClient;
}
