# Use a Python base image that includes build tools
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Install Node.js, npm, and curl
RUN apt-get update && \
    apt-get install -y curl nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Install the "uv" Python package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to the PATH for subsequent commands
ENV PATH="/root/.local/bin:$PATH"

# Copy all project files into the container
# (we will use .dockerignore to exclude unnecessary files)
COPY . .

# Install Python dependencies using uv
RUN uv sync

# Install frontend dependencies and build the static files
RUN npm --prefix frontend install
RUN npm --prefix frontend run build

# Tell Docker that the container will listen on port 8000
EXPOSE 8000

# The command to run when the container starts
CMD ["/app/.venv/bin/uvicorn", "api_job_search:app", "--host", "0.0.0.0", "--port", "8000"] 