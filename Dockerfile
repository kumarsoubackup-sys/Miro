FROM python:3.11

# Install Node.js (>=18) and required tooling
RUN apt-get update \
  && apt-get install -y --no-install-recommends nodejs npm \
  && rm -rf /var/lib/apt/lists/*

# Copy `uv` from the official image
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /uvx /bin/

WORKDIR /app

# Copy dependency manifests first to maximize layer caching
COPY package.json package-lock.json ./
COPY frontend/package.json frontend/package-lock.json ./frontend/
COPY backend/pyproject.toml backend/uv.lock ./backend/

# Install dependencies (Node + Python)
# Use CPU-only PyTorch to avoid downloading ~3GB of CUDA libraries
RUN npm ci \
  && npm ci --prefix frontend \
  && cd backend && UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu uv sync --frozen

# Copy project sources
COPY . .

EXPOSE 3000 5001

# Start frontend and backend together (development mode)
CMD ["npm", "run", "dev"]
