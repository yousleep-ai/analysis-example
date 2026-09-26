# Any base image can be used; the platform sees only the contract.
FROM python:3.12-slim
WORKDIR /app
LABEL org.opencontainers.image.source="https://github.com/raphaelvallat/yasa"
LABEL org.opencontainers.image.licenses="BSD-3-Clause"
# LightGBM, YASA's classifier, needs the OpenMP runtime, which the slim
# image does not carry.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*
# requirements.txt is the full, compiled lock (see requirements.in).
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps -r requirements.txt \
 && python -c "import mne, yasa, lightgbm, yousleep_common"
# The root filesystem is read-only on the platform; /tmp is writable.
ENV MPLCONFIGDIR=/tmp/matplotlib
COPY analysis.py .
ENTRYPOINT ["python3", "analysis.py"]
