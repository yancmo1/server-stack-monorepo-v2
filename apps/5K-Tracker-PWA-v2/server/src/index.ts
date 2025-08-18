import Fastify from 'fastify';
import cors from '@fastify/cors';
import multipart from '@fastify/multipart';

const fastify = Fastify({
  logger: true
});

async function start() {
  try {
    // Register plugins
    await fastify.register(cors, {
      origin: ['http://localhost:7777'],
      credentials: true
    });
    
    await fastify.register(multipart);

    // Health check
    fastify.get('/api/health', async () => {
      return { ok: true, timestamp: new Date().toISOString() };
    });

    // Simple test route
    fastify.get('/api/test', async () => {
      return { message: 'Server is working!' };
    });

    const port = Number(process.env.PORT) || 7778;
    await fastify.listen({ port, host: '0.0.0.0' });
    
    console.log(`🚀 Server running on http://localhost:${port}`);
    
    // Keep the process alive
    process.on('SIGTERM', () => {
      console.log('SIGTERM signal received: closing HTTP server');
      fastify.close();
    });

    process.on('SIGINT', () => {
      console.log('SIGINT signal received: closing HTTP server');
      fastify.close();
    });

  } catch (err) {
    console.error('Error starting server:', err);
    fastify.log.error(err);
    process.exit(1);
  }
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('Uncaught Exception:', error);
  process.exit(1);
});

start();