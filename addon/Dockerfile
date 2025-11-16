ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.18
# Multi-stage build for optimized image size

###############################
# Build stage
###############################
FROM $BUILD_FROM AS builder

# Install build dependencies
RUN apk add --no-cache \
    python3=~3.11 \
    py3-pip \
    python3-dev \
    gcc \
    g++ \
    musl-dev \
    linux-headers \
    libffi-dev \
    openssl-dev \
    cargo \
    rust

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

###############################
# Runtime stage
###############################
FROM $BUILD_FROM

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apk add --no-cache \
    python3=~3.11 \
    py3-pip \
    libstdc++ \
    libgcc \
    && ln -sf python3 /usr/bin/python

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Copy application files
COPY rootfs /

# Create necessary directories
RUN mkdir -p /data/models \
    /data/history \
    /data/logs \
    && chmod a+x /run.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8099/health || exit 1

# Labels
LABEL \
    io.hass.name="Wine Fermentation Monitor" \
    io.hass.description="Advanced wine fermentation monitoring with ML-powered predictions" \
    io.hass.arch="${BUILD_ARCH}" \
    io.hass.type="addon" \
    io.hass.version="${BUILD_VERSION}" \
    maintainer="TipsyHomeLab" \
    org.opencontainers.image.title="Wine Fermentation Monitor" \
    org.opencontainers.image.description="Advanced wine fermentation monitoring with ML-powered predictions" \
    org.opencontainers.image.vendor="TipsyHomeLab" \
    org.opencontainers.image.authors="TipsyHomeLab" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.source="https://github.com/tipsyhomelab/wine-fermentation-monitor"

# Set the entry point
CMD ["/run.sh"]
