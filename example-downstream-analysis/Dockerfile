# Any Python yousleep-common supports will do; a slim official image carries
# one with pip and nothing else.
FROM python:3.12-slim

# Make working directory
WORKDIR /app

# Add container metadata labels
LABEL org.opencontainers.image.source="https://github.com/yousleep-ai/analysis-example"
LABEL org.opencontainers.image.description="Example Downstream Analysis"
LABEL org.opencontainers.image.licenses="Apache-2.0"

# Install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the source code
COPY example-downstream-analysis.py /app/example-downstream-analysis.py

# Run the analysis: the portal passes --manifest-file and nothing else
ENTRYPOINT ["python3", "example-downstream-analysis.py"]
