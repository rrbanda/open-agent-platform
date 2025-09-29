# Production-grade Containerfile for Mortgage Agents System
# Using Red Hat Universal Base Image 9 with Python 3.11
FROM registry.redhat.io/ubi9/python-311:1-77

# Production environment variables
ENV APP_HOME=/opt/app-root/src/mortgage-agents \
    PYTHONPATH=/opt/app-root/src/mortgage-agents \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create application user (OpenShift compatible - random UID, GID 0)
USER root
RUN mkdir -p ${APP_HOME} && \
    chgrp -R 0 ${APP_HOME} && \
    chmod -R g=u ${APP_HOME}

# Set working directory
WORKDIR ${APP_HOME}

# Copy requirements first for better Docker layer caching
COPY --chown=1001:0 requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (excluding venv and other unnecessary files)
COPY --chown=1001:0 app/ ./app/
COPY --chown=1001:0 docs/ ./docs/

# Create directories for runtime data with proper permissions
RUN mkdir -p ./data ./logs ./config && \
    chgrp -R 0 ./data ./logs ./config && \
    chmod -R g=u ./data ./logs ./config

# Copy default configuration template (will be overridden by ConfigMap)
COPY --chown=1001:0 app/utils/config.yaml ./config/config-template.yaml

# Set proper permissions for OpenShift SCC compatibility (user 1001 already exists)
RUN chgrp -R 0 /opt/app-root && \
    chmod -R g=u /opt/app-root

# Switch to non-root user
USER 1001

# Set working directory to app/ where langgraph.json is located
WORKDIR ${APP_HOME}/app

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:2024/health')" || exit 1

# Expose port for LangGraph development server
EXPOSE 2024

# Default command (can be overridden in OpenShift deployment)
CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "2024", "--no-browser"]
