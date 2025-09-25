# ActCLI Semhost — Production Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml README.md ./
COPY src ./src

# Optional: Copy SPA build if serving from Semhost
# COPY studio/dist ./studio/dist

# Install dependencies and create non-root user
RUN pip install --no-cache-dir .[dev] && \
    useradd -m app && \
    chown -R app:app /app && \
    mkdir -p /mnt/ro /out /mnt/rw && \
    chown app:app /out /mnt/rw

# Switch to non-root user
USER app

# Environment variables
ENV SEMHOST_BIND=0.0.0.0
ENV SEMHOST_PORT=7530
ENV SEMHOST_CLI_DISABLE_TOOLS=1
ENV ACTCLI_REQUIRE_AUTH=0

# Expose port
EXPOSE 7530

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7530/health || exit 1

# Start command
CMD ["uvicorn", "semhost.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "7530"]