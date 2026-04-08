# Ai-school-openenv

OpenEnv-compliant environment for school operations evaluation.

## Quick Start

```bash
docker build -t ai-school-openenv .
docker run -p 7860:7860 ai-school-openenv
```

## API

```
POST /reset → Observation
POST /step → (obs, reward, done, info)
GET /state → State
```

## Validator Test

```bash
curl -X POST http://localhost:7860/reset
```

## Baseline

```bash
python inference.py
```

Dockerfile, inference.py, app.py at root for hackathon Phase 1.
