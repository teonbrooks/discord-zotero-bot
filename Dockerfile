FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first so Docker can cache the install layer
COPY pyproject.toml uv.lock ./

# Install production dependencies into the project virtual environment
RUN uv sync --frozen --no-dev

# Copy source files
COPY *.py ./

# Make the venv's Python the default for CMD
ENV PATH="/app/.venv/bin:$PATH"

CMD ["python", "zotero-bot.py"]
