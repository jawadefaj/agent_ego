FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
# Install essential packages only
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    xvfb \
    x11vnc \
    xfce4 \
    git \
    wget \
    curl \
    ca-certificates \
    # Chrome dependencies
    libnss3 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libglib2.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libasound2 \
    libatspi2.0-0 \
    libpango-1.0-0 \
    libegl1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Set Python 3.11 as the default python command
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1
# Install Google Chrome
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Install noVNC for browser-based access
RUN mkdir -p /opt && cd /opt && \
    git clone https://github.com/novnc/noVNC.git && \
    cd noVNC && git checkout v1.3.0 && \
    cd .. && \
    git clone https://github.com/novnc/websockify.git && \
    cd websockify && git checkout v0.10.0
# Create mount point for persistent storage
RUN mkdir -p /data
# Install Python dependencies
RUN pip3 install --upgrade pip && \
    pip3 install \
    playwright==1.50.0 \
    pyyaml \
    httpx \
    langchain \
    langchain-core \
    python-dotenv \
    # Add LangChain integrations
    langchain-openai \
    langchain-anthropic \
    langchain-deepseek \
    openai \
    anthropic \
    deepseek-ai
# Install Playwright browser to disk
ENV PLAYWRIGHT_BROWSERS_PATH=/data/playwright-browsers
RUN mkdir -p $PLAYWRIGHT_BROWSERS_PATH && \
    python3 -m playwright install chromium && \
    python3 -m playwright install-deps chromium
# Create working directory
WORKDIR /app
# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
ENV PLAYWRIGHT_BROWSERS_PATH=/data/playwright-browsers
# Create startup script
RUN echo '#!/bin/bash\n\
# Start X server\n\
Xvfb :99 -screen 0 1920x1080x24 -ac &\n\
export DISPLAY=:99\n\
\n\
# Start XFCE desktop environment\n\
xfce4-session &\n\
\n\
# Start VNC server without password\n\
x11vnc -forever -display :99 -rfbport 5900 -nopw -shared -nowf -xkb &\n\
\n\
# Start noVNC web server\n\
/opt/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6080 &\n\
\n\
echo "========================================================="\n\
echo "🔍 VISUALIZATION AVAILABLE:"\n\
echo "Web browser: http://localhost:6080/vnc.html"\n\
echo "VNC client: localhost:5900"\n\
echo "No password required"\n\
echo "========================================================="\n\
\n\
# Keep the container running\n\
tail -f /dev/null\n\
' > /app/start.sh
# Make scripts executable
RUN chmod +x /app/start.sh
# Expose ports for VNC and noVNC
EXPOSE 5900 6080
# Set the default command
CMD ["/app/start.sh"]