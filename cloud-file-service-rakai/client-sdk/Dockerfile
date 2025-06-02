FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY setup.py .
COPY cloudservice ./cloudservice

# Install the SDK in development mode
RUN pip install -e .

# Install additional tools for testing
RUN pip install pytest httpx

# Copy example files
COPY example.py .
COPY README.md .

# Command to run the example
CMD ["python", "example.py"]
