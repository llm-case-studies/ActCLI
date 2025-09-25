# ActCLI Docker Deployment

This directory contains Docker deployment files for ActCLI Semhost.

## Quick Start

```bash
# From the project root
docker compose -f docker/compose.yml up --build
```

The service will be available at http://localhost:7530

## Directory Structure

- `compose.yml` - Docker Compose configuration
- `Dockerfile` - Production container image
- `README.md` - This file

## Volume Mounts

- `./ro:/mnt/ro:ro` - Read-only mount for input files (Excel, etc.)
- `./out:/out` - Output directory for artifacts and logs
- `./work:/mnt/rw` - Optional read-write workspace

## Environment Variables

- `SEMHOST_BIND` - Bind address (default: 0.0.0.0)
- `SEMHOST_PORT` - Port to listen on (default: 7530)
- `SEMHOST_CORS_ORIGINS` - Allowed CORS origins for SPA
- `SEMHOST_CLI_DISABLE_TOOLS` - Disable CLI MCP tools (default: "1")
- `ACTCLI_REQUIRE_AUTH` - Require authentication (default: "0")

## Usage

1. Place Excel files in `./ro/` directory
2. Start the service: `docker compose -f docker/compose.yml up`
3. Access the SPA at http://localhost:7530/ui (if SPA is built into the image)
4. Or use API directly at http://localhost:7530/

## Development

For development with hot reload:
```bash
# Run SPA separately
cd studio && npm run dev

# Run Semhost with local changes
uvicorn semhost.main:create_app --factory --host 127.0.0.1 --port 7530 --reload
```

## Production Notes

- The container runs as non-root user `app`
- Health checks are configured for container orchestration
- Logs are written to stdout/stderr for container log collection
- Artifacts are written to the mounted `/out` volume