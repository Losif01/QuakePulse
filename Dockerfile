#smol and stable python version
FROM python:3.12-slim

WORKDIR /app

#install uv system-wide (idc about the user choices, no uv means no proper project)
RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

# CRITICAL FIX 1: Tell uv to copy files instead of symlinking,
# and compile bytecode for faster startup
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

#--frozen ensures it strictly follows uv.lock without trying to update
RUN uv sync --frozen --no-install-project --no-dev

#copy the rest of app code
COPY . .

RUN uv sync --frozen --no-dev

#add the uv virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"
