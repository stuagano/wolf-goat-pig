# Playwright test container for Wolf-Goat-Pig frontend
FROM mcr.microsoft.com/playwright:v1.41.0-focal

# Set working directory
WORKDIR /app

# Copy package files
COPY tests/e2e/package*.json ./tests/e2e/
COPY frontend/package*.json ./frontend/

# Install dependencies for e2e tests
WORKDIR /app/tests/e2e
RUN npm ci

# Install frontend dependencies (needed to build)
WORKDIR /app/frontend
RUN npm ci

# Copy source code
WORKDIR /app
COPY tests/e2e ./tests/e2e
COPY frontend ./frontend

# Build frontend
WORKDIR /app/frontend
RUN npm run build

# Set environment variables
ENV CI=true
ENV NODE_ENV=production

# Return to e2e directory
WORKDIR /app/tests/e2e

# Run Playwright tests
CMD ["npx", "playwright", "test", "--reporter=list"]
