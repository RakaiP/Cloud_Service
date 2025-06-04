/**
 * Example usage of the Cloud File Service SDK
 * 
 * This demonstrates the complete upload/download flow
 * using our tested backend services.
 */

const { CloudFileClient } = require('./cloud-file-sdk');
const fs = require('fs');

// Configuration based on your working setup
const config = {
    metadataServiceUrl: 'http://localhost:8000',
    blockStorageUrl: 'http://localhost:8003',
    auth0Domain: 'dev-mc721bw3z72t3xex.us.auth0.com',
    apiAudience: 'https://cloud-api.rakai/',
    chunkSize: 1024 * 1024 // 1MB chunks (tested optimal size)
};

// Your Auth0 token (get from .env or Auth0 dashboard)
const AUTH_TOKEN = process.env.AUTH0_TOKEN || 'your-token-here';

async function demonstrateSDK() {
    try {
        // Initialize client
        const client = new CloudFileClient(config);
        client.setToken(AUTH_TOKEN);
        
        console.log('🚀 Cloud File Service SDK Demo');
        console.log('================================');
        
        // Create a test file
        const testFileName = 'sdk-demo-file.txt';
        const testContent = `SDK Demo File
Created: ${new Date().toISOString()}
Content: This file demonstrates the Cloud File Service SDK
Features: Chunking, upload, download, metadata tracking
Backend: Tested with block storage + metadata services

This file will be split into chunks and uploaded to MinIO
through the block storage service, with metadata tracked
in PostgreSQL through the metadata service.
`;
        
        fs.writeFileSync(testFileName, testContent);
        console.log(`✅ Created test file: ${testFileName} (${testContent.length} bytes)`);
        
        // 1. Upload the file
        console.log('\n📤 Uploading file...');
        const uploadResult = await client.uploadFile(testFileName, {
            onProgress: (progress) => {
                console.log(`  Chunk ${progress.chunkIndex} uploaded (${progress.chunkSize} bytes)`);
            }
        });
        
        console.log(`✅ Upload successful!`);
        console.log(`   File ID: ${uploadResult.fileId}`);
        console.log(`   Size: ${uploadResult.size} bytes`);
        console.log(`   Chunks: ${uploadResult.chunks}`);
        
        // 2. List files
        console.log('\n📋 Listing files...');
        const files = await client.listFiles();
        console.log(`✅ Found ${files.length} files:`);
        files.forEach(file => {
            console.log(`   - ${file.filename} (ID: ${file.file_id})`);
        });
        
        // 3. Download the file
        console.log('\n📥 Downloading file...');
        const downloadedFileName = 'downloaded-' + testFileName;
        await client.downloadFile(uploadResult.fileId, downloadedFileName);
        
        // 4. Verify the download
        const originalContent = fs.readFileSync(testFileName, 'utf8');
        const downloadedContent = fs.readFileSync(downloadedFileName, 'utf8');
        
        if (originalContent === downloadedContent) {
            console.log('✅ Download successful - content matches!');
        } else {
            console.log('❌ Download failed - content mismatch!');
        }
        
        // 5. Clean up
        console.log('\n🧹 Cleaning up...');
        fs.unlinkSync(testFileName);
        fs.unlinkSync(downloadedFileName);
        
        // Optionally delete from cloud (uncomment to test deletion)
        // await client.deleteFile(uploadResult.fileId);
        // console.log('✅ File deleted from cloud');
        
        console.log('\n🎉 SDK demonstration completed successfully!');
        
    } catch (error) {
        console.error('❌ SDK Demo failed:', error.message);
        console.error('Details:', error);
        
        // Troubleshooting tips
        console.log('\n💡 Troubleshooting:');
        console.log('1. Make sure all services are running: docker-compose up');
        console.log('2. Check your Auth0 token is valid and not expired');
        console.log('3. Verify services are healthy:');
        console.log('   - http://localhost:8000/health (metadata)');
        console.log('   - http://localhost:8003/health (block storage)');
        console.log('4. Update AUTH0_TOKEN in your .env file if needed');
    }
}

// Run the demo
if (require.main === module) {
    demonstrateSDK();
}

module.exports = { demonstrateSDK };
