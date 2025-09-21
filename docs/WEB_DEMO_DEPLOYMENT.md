# Web Demo Deployment Scenarios

**Primary Focus**: ActCLI is designed for local deployment and development workflows. However, web demos provide an accessible way for users to experience the platform before committing to local installation.

## Deployment Matrix

| Component | Local (Primary) | Team Demo | Public Demo |
|-----------|----------------|-----------|-------------|
| **ActCLI CLI** | Native binary | Docker dev container | Browser-based terminal |
| **Semhost API** | Local process | Docker container | Container + Load balancer |
| **SPA Frontend** | Local dev server | Container | CDN + Container |
| **Ollama** | Local server | Shared GPU server | Cloud GPU (RunPod/Vast) |
| **Models** | ./models/ directory | Network storage | Pre-loaded cloud instances |

## Scenario 1: Local Development (Primary Use Case)

**Target**: Individual developers, small teams, production actuarial workflows

```bash
# Everything runs locally for maximum performance and control
actcli                              # Start CLI (port varies)
uvicorn semhost.main:create_app     # API layer (port 7530)
npm run dev                         # SPA frontend (port 5173)
ollama serve --port 11435           # Local models
```

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                         localhost                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ ActCLI      │  │ Semhost     │  │ SPA         │  │ Ollama  │ │
│  │ CLI         │──│ API         │──│ Frontend    │──│ Server  │ │
│  │ Native      │  │ :7530       │  │ :5173       │  │ :11435  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
│       │                  │                  │            │     │
│  ┌────▼────┐        ┌────▼────┐        ┌────▼────┐  ┌────▼───┐ │
│  │ Git     │        │ Session │        │ Browser │  │ Models │ │
│  │ Projects│        │ State   │        │ UI      │  │ 50GB+  │ │
│  └─────────┘        └─────────┘        └─────────┘  └────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits:**
- ✅ **Performance**: Direct GPU/CPU access, no network latency
- ✅ **Security**: All data stays local, no cloud dependencies
- ✅ **Integration**: Native git, file system, environment access
- ✅ **Cost**: Zero cloud costs, models cached locally
- ✅ **Reliability**: Works offline, no external service dependencies

---

## Scenario 2: Team Demo Environment

**Target**: Small teams, proof-of-concepts, shared development

```bash
# Shared server hosts containers, users access via CLI + web
docker-compose up                   # API + SPA + shared storage
ollama serve --host 0.0.0.0         # Shared GPU server
actcli --api-url https://team.company.com  # Remote CLI usage
```

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Team Server (IONOS/AWS)                     │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │ Nginx Proxy     │    │ Docker Stack                        │ │
│  │ - SSL/TLS       │    │  ┌─────────────┐ ┌─────────────────┐ │ │
│  │ - Port 443      │────┼──│ SPA         │ │ Semhost API     │ │ │
│  │ - Load balancer │    │  │ React/Vue   │ │ FastAPI+Uvicorn │ │ │
│  └─────────────────┘    │  └─────────────┘ └─────────────────┘ │ │
│                         │  ┌─────────────┐ ┌─────────────────┐ │ │
│                         │  │ Dev Env     │ │ Shared Storage  │ │ │
│                         │  │ Code-server │ │ Sessions/Models │ │ │
│                         │  └─────────────┘ └─────────────────┘ │ │
│                         └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                              │
          │                    ┌─────────▼──────────┐
          │                    │ GPU Server         │
          │                    │ - Ollama           │
          │                    │ - Tesla V100/A100  │
          │                    │ - 20+ models       │
          │                    └────────────────────┘
          │
┌─────────▼─────────┐    ┌─────────────────────────────────────┐
│ User Machines     │    │ User CLI Options                    │
│ - Browser access  │    │ Option A: Local install             │
│ - WebSocket live  │    │   curl install.sh | bash           │
│ - Shared sessions │    │ Option B: Dev container in browser  │
└───────────────────┘    │   team.company.com/dev/             │
                         └─────────────────────────────────────┘
```

**Benefits:**
- ✅ **Shared Resources**: One GPU server for multiple users
- ✅ **Collaboration**: Shared sessions, team model access
- ✅ **Easy Access**: Web UI + optional CLI download
- ✅ **Cost Efficient**: Shared infrastructure, moderate cloud costs

---

## Scenario 3: Public Web Demo

**Target**: Marketing, conferences, new user onboarding, showcase

```bash
# High-availability web demo with powerful GPU backing
demo.actcli.com                     # Public SPA with impressive models
api.actcli.com                      # Scalable API backend
runpod/vast.ai                      # On-demand GPU instances
```

**Architecture:**
```
┌─────────────────────────────────────────────────────────────────┐
│                    IONOS VPS (Frontend)                        │
│  ┌─────────────────┐    ┌─────────────────────────────────────┐ │
│  │ Nginx + SSL     │    │ Container Orchestration             │ │
│  │ - Cloudflare    │    │  ┌─────────────┐ ┌─────────────────┐ │ │
│  │ - CDN           │────┼──│ SPA Demo    │ │ Semhost API     │ │ │
│  │ - Auto-scaling  │    │  │ - Showcase  │ │ - Rate limiting │ │ │
│  └─────────────────┘    │  │ - Examples  │ │ - Auth optional │ │ │
│                         │  └─────────────┘ └─────────────────┘ │ │
│                         │  ┌─────────────┐ ┌─────────────────┐ │ │
│                         │  │ VS Code Web │ │ Demo Analytics  │ │ │
│                         │  │ - Try CLI   │ │ - Usage metrics │ │ │
│                         │  └─────────────┘ └─────────────────┘ │ │
│                         └─────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                    │
          ┌─────────▼─────────────────────────────────────────────┐
          │              RunPod GPU Fleet                         │
          │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
          │  │ Instance 1  │  │ Instance 2  │  │ Auto-scaling    │ │
          │  │ H100 GPU    │  │ A100 GPU    │  │ - Spin up/down  │ │
          │  │ Llama3:70B  │  │ Claude-3    │  │ - Cost optimize │ │
          │  │ GPT-4       │  │ Mixtral     │  │ - Load balance  │ │
          │  └─────────────┘  └─────────────┘  └─────────────────┘ │
          └───────────────────────────────────────────────────────┘
                    │
          ┌─────────▼─────────┐
          │ Global Users      │
          │ - Live roundtables│
          │ - Model comparison│
          │ - Real-time demos │
          │ - Download CLI    │
          └───────────────────┘
```

**Features:**
- 🎯 **Impressive Demos**: 70B+ models, complex roundtables
- 🎯 **Zero Friction**: Instant access, no signup required
- 🎯 **Showcase Power**: Side-by-side model comparisons
- 🎯 **Conversion Path**: Easy CLI download for local use

---

## Cost Analysis

| Scenario | Monthly Cost | Use Case | Performance |
|----------|-------------|----------|-------------|
| **Local** | $0 | Production, development | Excellent |
| **Team Demo** | €50-200 | Small teams, POCs | Good |
| **Public Demo** | $200-1000 | Marketing, showcases | Exceptional |

## Implementation Priority

1. **Phase 1**: Perfect local deployment (primary value)
2. **Phase 2**: Team demo for collaboration
3. **Phase 3**: Public demo for marketing/onboarding

## Technology Stack Summary

**Frontend**: React/Vue SPA with WebSocket streaming
**API**: FastAPI + Uvicorn with CORS for browser access
**Models**: Ollama (local) or cloud GPU services (demo)
**Deployment**: Docker containers with Nginx proxy
**Infrastructure**: IONOS (web) + RunPod/Vast (GPU) for demos

---

**Key Principle**: Web demos are onramps to local deployment. The goal is to showcase ActCLI's power and drive adoption of the primary local-first architecture.