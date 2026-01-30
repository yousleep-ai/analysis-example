FROM ubuntu:22.04

# Make working directory
WORKDIR /app
RUN mkdir -p /app

# Add container metadata labels
LABEL org.opencontainers.image.source="https://github.com/yousleep-ai/analysis-example"
LABEL org.opencontainers.image.description="Example Downstream Analysis"
LABEL org.opencontainers.image.licenses="Proprietary"

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# Copy the source code
COPY example-downstream-analysis.py /app/example-downstream-analysis.py

# Run the analysis
ENTRYPOINT ["python3", "example-downstream-analysis.py"]
