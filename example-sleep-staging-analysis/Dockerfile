# yousleep-common needs Python 3.12 or newer; a slim official image carries it
# with pip and nothing else.
FROM python:3.12-slim

# Make working directory
WORKDIR /app

# Add container metadata labels
LABEL org.opencontainers.image.source="https://github.com/yousleep-ai/analysis-example"
LABEL org.opencontainers.image.description="Example Sleep Staging Analysis"
LABEL org.opencontainers.image.licenses="Proprietary"

# Install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the source code
COPY example-sleep-staging-analysis.py /app/example-sleep-staging-analysis.py

# Run the analysis: the portal passes --manifest-file and nothing else
ENTRYPOINT ["python3", "example-sleep-staging-analysis.py"]
