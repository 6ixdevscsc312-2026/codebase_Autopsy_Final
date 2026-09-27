FROM python:3.11-slim

# git: needed to clone repos passed to /api/analyze
# curl: needed to install Node.js and Bob Shell
RUN apt-get update && apt-get install -y --no-install-recommends git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Bob Shell requires Node.js 22.15+ — not present in python:3.11-slim by
# default, so install it explicitly before the Bob install script runs.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && node --version

# Install the real Bob Shell CLI so non-mock (real=True) runs work in
# deployment, not just locally. Requires network at *build* time, which
# this Dockerfile has (unlike a network-restricted dev sandbox).
RUN curl -fsSL https://bob.ibm.com/download/bobshell.sh | bash

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY autopsy/ autopsy/
COPY static/ static/

# BOB_API_KEY is read from the environment at runtime — set it as a
# secret in your hosting platform's dashboard, never bake it into the
# image or commit it to the repo.
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn autopsy.webapp:app --host 0.0.0.0 --port ${PORT}"]
