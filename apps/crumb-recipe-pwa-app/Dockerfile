# Simple single-stage build for Crumb PWA
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Clean install with esbuild rebuild to fix version mismatch
RUN rm -f package-lock.json && \
    npm cache clean --force && \
    npm install && \
    npm rebuild esbuild

# Copy all source code
COPY . .

# Build the frontend
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Set ownership
RUN chown -R nodejs:nodejs /app
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "const http = require('http'); const options = { host: 'localhost', port: 3000, path: '/health', timeout: 2000 }; const req = http.request(options, (res) => { if (res.statusCode === 200) process.exit(0); else process.exit(1); }); req.on('error', () => process.exit(1)); req.end();"

# Start the application
CMD ["node", "server/index.js"]