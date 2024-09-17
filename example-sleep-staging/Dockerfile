FROM ubuntu:22.04

# Make working directory
WORKDIR /app
RUN mkdir -p /app

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip

# Install Python packages
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# Copy the source code
COPY example-sleep-staging.py /app/example-sleep-staging.py

# Run the analysis
ENTRYPOINT ["python3", "example-sleep-staging.py"]
