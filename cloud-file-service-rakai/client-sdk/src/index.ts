import express, { Request, Response } from 'express';
import * as dotenv from 'dotenv';
import { AddressInfo } from 'net';

// Load environment variables
dotenv.config();

const app = express();
const port = process.env.PORT ? parseInt(process.env.PORT) : 8080;

// Health check endpoint
app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'healthy' });
});

// Start server with error handling
const server = app.listen(port, () => {
  const address = server.address() as AddressInfo;
  console.log(`Server running on port ${address.port}`);
}).on('error', (err: Error) => {
  console.error('Server failed to start:', err);
  process.exit(1);
});

export default app;