# 🚀 Deployment Guide

Complete guide for deploying the School Operations Environment to Hugging Face Spaces and other platforms.

---

## Hugging Face Spaces Deployment

### Step 1: Create a Space

1. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
2. Fill in the form:
   - **Space name:** `school-operations-env`
   - **License:** MIT
   - **Space SDK:** Docker
3. Add tags: `openenv`, `benchmark`, `school-operations`, `ai-agents`
4. Click "Create Space"

### Step 2: Connect Repository

```bash
# Clone the space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/school-operations-env
cd school-operations-env

# Add your project files
cp -r /path/to/local/school-operations-env/* .

# Commit and push
git add .
git commit -m "Initial commit: OpenEnv school operations environment"
git push
```

### Step 3: Add Secrets (for baseline inference)

In the Space settings:
1. Go to **Settings → Secrets**
2. Add `HF_TOKEN`: Your OpenAI API key
3. Save

### Step 4: Monitor Deployment

- The Space will auto-build from the Dockerfile
- Check **Logs** tab for build progress
- Once built, your Space is live at:
  ```
  https://huggingface.co/spaces/YOUR_USERNAME/school-operations-env
  ```

---

## Docker Local Deployment

### Build Image

```bash
docker build -t school-operations-env:v1.0 .
```

### Run Container

```bash
# Interactive mode with volume mount
docker run -it \
  -v $(pwd):/app \
  -e HF_TOKEN="your-openai-api-key" \
  -p 7860:7860 \
  school-operations-env:v1.0 \
  python app.py
```

### Run Baseline in Container

```bash
docker run -it \
  -e HF_TOKEN="your-openai-api-key" \
  school-operations-env:v1.0 \
  python baseline_inference.py
```

---

## Kubernetes Deployment

### Create ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: school-ops-config
data:
  MAX_STEPS_EASY: "5"
  MAX_STEPS_MEDIUM: "10"
  MAX_STEPS_HARD: "15"
```

### Create Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: school-ops-secrets
type: Opaque
stringData:
  HF_TOKEN: "your-openai-api-key"
```

### Create Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: school-operations-env
spec:
  replicas: 2
  selector:
    matchLabels:
      app: school-ops
  template:
    metadata:
      labels:
        app: school-ops
    spec:
      containers:
      - name: app
        image: school-operations-env:v1.0
        ports:
        - containerPort: 7860
        env:
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: school-ops-secrets
              key: HF_TOKEN
        envFrom:
        - configMapRef:
            name: school-ops-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### Deploy

```bash
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
```

---

## AWS Deployment

### Using ECR and Lambda

```bash
# Create ECR repository
aws ecr create-repository --repository-name school-operations-env

# Build and push
docker build -t school-operations-env:latest .
docker tag school-operations-env:latest \
  ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/school-operations-env:latest
docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/school-operations-env:latest
```

### Using ECS

Create task definition with:
- Image: Your ECR image URI
- Memory: 512 MB
- CPU: 256
- Environment: HF_TOKEN
- Port mappings: 7860:7860

---

## Environment Variables

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `HF_TOKEN` | OpenAI API key | None | Yes (for baseline) |
| `PYTHONUNBUFFERED` | Unbuffered output | 1 | No |
| `HF_HOME` | Hugging Face cache | ~/.cache | No |

---

## Health Checks

The Dockerfile includes a health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from environment import SchoolOperationsEnv; env = SchoolOperationsEnv(); env.reset()" || exit 1
```

---

## Troubleshooting

### Build Failures

**Error:** `pip install failed`
- **Solution:** Check Python version compatibility (3.10+)
- Ensure all requirements are correct

**Error:** `Module not found`
- **Solution:** Verify all Python files are in the build context
- Check .dockerignore isn't excluding necessary files

### Runtime Errors

**Error:** `OpenAI API error`
- **Solution:** Verify HF_TOKEN/OPENAI_API_KEY is set
- Check API key is valid and has sufficient quota

**Error:** `Port already in use`
- **Solution:** Use different port: `docker run -p 8000:7860 ...`

---

## Performance Tips

1. **Caching:** Docker builds cache layers - put stable dependencies first
2. **Multi-stage builds:** Use for smaller final images
3. **Resource limits:** Set appropriate memory/CPU constraints
4. **Load balancing:** Use reverse proxy for multiple instances

---

## Security Checklist

- [ ] API keys stored in environment variables (not in code)
- [ ] Secrets managed through platform secrets manager
- [ ] Image scanned for vulnerabilities
- [ ] Non-root user in Dockerfile (recommended)
- [ ] Network policies restrict traffic (if using Kubernetes)

---

## Monitoring

### Logs

```bash
# Local Docker
docker logs CONTAINER_ID

# Kubernetes
kubectl logs deployment/school-operations-env

# Hugging Face Spaces
Check in Space interface under Logs
```

### Metrics

Key metrics to track:
- API response time
- Grader execution time
- Memory usage
- Error rates

---

## Rollback Procedures

### Docker

```bash
# Switch to previous image
docker run -d --name app-old school-operations-env:v0.9
```

### Kubernetes

```bash
kubectl rollout history deployment/school-operations-env
kubectl rollout undo deployment/school-operations-env --to-revision=1
```

### Hugging Face Spaces

- Space automatically keeps previous versions
- Restore from Settings → Space versions
