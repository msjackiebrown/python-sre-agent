# Deployment: Running in Different Environments

Guide for local development, remote servers, and cloud platforms.

---

## Local Development (Recommended for Testing)

### Prerequisite: Ollama Running Locally

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: In a separate terminal, run the app
streamlit run src/main.py
```

**Advantages:**
- ✅ Full control
- ✅ Fast iteration
- ✅ Easy debugging
- ✅ No infrastructure

**Performance:**
- Inference: ~2-3 seconds per query
- UI: Instant (local network)

---

## Remote Ollama + Local UI

For testing with a more powerful inference server:

```bash
# On the Ollama server (powerful machine, 24GB+ RAM)
ssh user@ollama-server.com
ollama serve --host 0.0.0.0:11434

# On your local machine
export OLLAMA_HOST=http://ollama-server.com:11434
export OLLAMA_MODEL=qwen3.8:27b
streamlit run src/main.py
```

**Advantages:**
- ✅ Use larger models (Qwen 3.8-27B)
- ✅ Better reasoning
- ✅ Test before deploying

**Performance:**
- Inference: ~5-10 seconds per query
- UI: Same (local network to remote server)

**Networking:**
```bash
# Test connectivity
curl http://ollama-server.com:11434/api/tags

# Verify model is available
# Should see qwen3.8:27b in the response
```

---

## Docker: Single Container

Run the entire app in Docker (Ollama + UI).

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Ollama (optional, or use a separate Ollama container)
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy application
COPY . .

# Expose Streamlit port
EXPOSE 8501
# Expose Ollama port
EXPOSE 11434

# Start both services
CMD ["sh", "-c", "ollama serve & sleep 2 && streamlit run src/main.py --server.port=8501 --server.address=0.0.0.0"]
```

### Build and Run

```bash
docker build -t sre-agent .

docker run -p 8501:8501 -p 11434:11434 sre-agent
```

**Access:**
- UI: http://localhost:8501
- Ollama API: http://localhost:11434

**Advantages:**
- ✅ Reproducible environment
- ✅ Easy deployment
- ✅ Isolation

**Disadvantages:**
- ❌ Larger image (Python + Ollama)
- ❌ Higher memory footprint

---

## Docker Compose: Separate Services

Better practice: Separate Ollama and UI containers.

### docker-compose.yml

```yaml
version: "3.8"

services:
  ollama:
    image: ollama/ollama:latest
    container_name: sre-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      OLLAMA_HOST: 0.0.0.0:11434
    command: serve

  agent:
    build:
      context: .
      dockerfile: Dockerfile.app
    container_name: sre-agent
    ports:
      - "8501:8501"
    environment:
      OLLAMA_HOST: http://ollama:11434
      OLLAMA_MODEL: qwen2.5:7b
    depends_on:
      - ollama
    volumes:
      - ./src:/app/src
      - ./src/data:/app/src/data

volumes:
  ollama_data:
```

### Dockerfile.app

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "src/main.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
```

### Run

```bash
docker-compose up --build
```

**Access:**
- UI: http://localhost:8501
- Ollama API: http://localhost:11434

**Advantages:**
- ✅ Scalable architecture
- ✅ Easy to upgrade each service independently
- ✅ Better failure isolation

---

## Kubernetes: Production Deployment

For large-scale deployment.

### k8s/namespace.yaml

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sre-agent
```

### k8s/ollama-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: sre-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
      - name: ollama
        image: ollama/ollama:latest
        ports:
        - containerPort: 11434
        env:
        - name: OLLAMA_HOST
          value: "0.0.0.0:11434"
        resources:
          requests:
            memory: "24Gi"
            cpu: "4"
          limits:
            memory: "32Gi"
            cpu: "8"
        volumeMounts:
        - name: ollama-data
          mountPath: /root/.ollama
      volumes:
      - name: ollama-data
        persistentVolumeClaim:
          claimName: ollama-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: sre-agent
spec:
  selector:
    app: ollama
  ports:
  - protocol: TCP
    port: 11434
    targetPort: 11434
  type: ClusterIP
```

### k8s/agent-deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sre-agent
  namespace: sre-agent
spec:
  replicas: 3  # Scale horizontally
  selector:
    matchLabels:
      app: sre-agent
  template:
    metadata:
      labels:
        app: sre-agent
    spec:
      containers:
      - name: agent
        image: sre-agent:latest
        ports:
        - containerPort: 8501
        env:
        - name: OLLAMA_HOST
          value: "http://ollama:11434"
        - name: OLLAMA_MODEL
          value: "qwen2.5:7b"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: sre-agent
  namespace: sre-agent
spec:
  selector:
    app: sre-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: LoadBalancer
```

### Deploy

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/ollama-deployment.yaml
kubectl apply -f k8s/agent-deployment.yaml

# Check status
kubectl get pods -n sre-agent

# Access via LoadBalancer IP
kubectl get svc -n sre-agent
```

**Advantages:**
- ✅ Highly scalable
- ✅ Automatic restart on failure
- ✅ Rolling updates
- ✅ Resource management

**Considerations:**
- ⚠️ Complex setup
- ⚠️ Requires Kubernetes cluster
- ⚠️ Higher infrastructure cost

---

## Cloud Platforms

### Streamlit Cloud (For UI Only)

Free hosting for the Streamlit UI.

**Prerequisites:**
- GitHub repository
- Remote Ollama instance (your own server or managed service)

**Steps:**

1. Push code to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect GitHub account
4. Create new app
5. Select repository and `src/main.py`
6. Set environment variables:
   ```
   OLLAMA_HOST = http://your-ollama-server:11434
   OLLAMA_MODEL = qwen2.5:7b
   ```

**Link your remote Ollama:**
```python
import os

# On Streamlit Cloud, these env vars are set
OLLAMA_HOST = os.getenv("OLLAMA_HOST")  # e.g., http://your-server:11434
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")  # e.g., qwen2.5:7b
```

**Advantages:**
- ✅ Free tier available
- ✅ Zero DevOps for UI
- ✅ Automatic HTTPS
- ✅ Auto-deploy on push

**Disadvantages:**
- ❌ UI only (separate Ollama instance required)
- ❌ Can't run Ollama on Streamlit Cloud (no GPU)

---

### AWS

#### Option 1: ECS + Fargate (Container Orchestration)

```bash
# Push image to ECR
aws ecr create-repository --repository-name sre-agent
aws ecr get-login-password | docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com
docker build -t sre-agent .
docker tag sre-agent:latest $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sre-agent:latest
docker push $AWS_ACCOUNT.dkr.ecr.$REGION.amazonaws.com/sre-agent:latest

# Create ECS task definition (see cloudformation.yaml)
# Deploy with Fargate for serverless containers
```

#### Option 2: EC2 + Docker Compose

```bash
# Launch EC2 instance (Ubuntu 20.04, t3.xlarge or larger)
# SSH into instance
ssh -i key.pem ubuntu@instance.com

# Install Docker
sudo apt-get update && sudo apt-get install -y docker.io docker-compose

# Clone repo
git clone https://github.com/yourusername/python-sre-agent.git
cd python-sre-agent

# Run
docker-compose up -d

# Access via instance IP
curl http://<instance-ip>:8501
```

**Advantages:**
- ✅ Full control
- ✅ GPU instance available
- ✅ Cost-effective (pay for what you use)

**Disadvantages:**
- ⚠️ Manual management
- ⚠️ Responsibility for updates/patches

---

### Google Cloud (GCP)

#### Cloud Run (Streamlit UI Only)

```bash
# Enable APIs
gcloud services enable run.googleapis.com

# Build and push image
gcloud builds submit --tag gcr.io/$PROJECT_ID/sre-agent

# Deploy
gcloud run deploy sre-agent \
  --image gcr.io/$PROJECT_ID/sre-agent:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OLLAMA_HOST=http://your-ollama-server:11434
```

**Advantages:**
- ✅ Serverless (no infrastructure)
- ✅ Auto-scaling
- ✅ HTTPS automatically

**Disadvantages:**
- ❌ No Ollama (stateless compute only)
- ⚠️ Cold starts (~30-60 seconds)

---

### Hugging Face Spaces (For Portfolio)

Free hosting with Streamlit support.

**Steps:**

1. Create account at [huggingface.co/spaces](https://huggingface.co/spaces)
2. New Space → Streamlit
3. Upload your repo files
4. Set environment variables in Space settings
5. App auto-deploys

**Advantages:**
- ✅ Free tier
- ✅ Built for ML projects
- ✅ Great for portfolio

**Disadvantages:**
- ❌ No Ollama (need remote instance)
- ⚠️ Can be slow (free tier)

---

## Comparison Matrix

| Platform | Ease | Cost | Scalability | Ollama | Best For |
|----------|------|------|-------------|--------|----------|
| **Local** | ⭐⭐⭐⭐⭐ | Free | 1 user | Local | Development |
| **Remote Ollama + Local UI** | ⭐⭐⭐⭐ | Variable | Few users | Remote | Testing advanced models |
| **Docker (Local)** | ⭐⭐⭐⭐ | Free | 1 user | Included | Reproducibility |
| **Docker Compose** | ⭐⭐⭐ | Free | Few users | Included | Development/Demo |
| **Kubernetes** | ⭐⭐ | $20-50/mo | 100+ users | Included | Production |
| **Streamlit Cloud** | ⭐⭐⭐⭐ | Free | Unlimited* | Remote only | Portfolio demo |
| **AWS ECS/Fargate** | ⭐⭐ | $10-50/mo | 1000+ users | EC2 separate | Enterprise |
| **GCP Cloud Run** | ⭐⭐⭐ | $0.50-10/mo | Auto-scale | No | Serverless web app |
| **Hugging Face Spaces** | ⭐⭐⭐⭐ | Free | Modest | Remote only | Portfolio demo |

*UI only; Ollama must be remote

---

## Environment Variables for Deployment

### Required
```bash
OLLAMA_HOST=http://localhost:11434    # Ollama server URL
OLLAMA_MODEL=qwen2.5:7b               # Model name
```

### Optional
```bash
STREAMLIT_SERVER_PORT=8501            # Streamlit port (default: 8501)
STREAMLIT_SERVER_ADDRESS=0.0.0.0      # Streamlit bind address
STREAMLIT_SERVER_HEADLESS=true        # Disable browser auto-open
```

### Streamlit Cloud
Set via Space Settings or secrets.toml:
```toml
# .streamlit/secrets.toml (DO NOT commit)
OLLAMA_HOST = "http://your-server:11434"
OLLAMA_MODEL = "qwen2.5:7b"
```

---

## Security Considerations

### For Production

1. **Authentication**
   - Add OAuth2 or JWT tokens
   - Restrict access to internal networks

2. **HTTPS/TLS**
   - Use Let's Encrypt certificates
   - Enable in load balancer (not app level)

3. **Rate Limiting**
   - Implement request throttling
   - Prevent abuse

4. **Monitoring**
   - Log all queries
   - Alert on errors/anomalies
   - Monitor resource usage

5. **Data Privacy**
   - Encrypt data at rest
   - Use VPCs for internal communication
   - Never log sensitive queries

---

## Troubleshooting Deployment

### "Connection refused" Error
```bash
# Check Ollama is running and accessible
curl http://ollama-server:11434/api/tags

# Verify firewall allows traffic
telnet ollama-server 11434
```

### "Model not found" in Deployed App
```bash
# SSH into Ollama server
ssh ollama-server

# Pull the model manually
ollama pull qwen2.5:7b

# Verify it's available
curl http://localhost:11434/api/tags
```

### Streamlit Cloud App Not Starting
```bash
# Check logs in Cloud UI
# Common issues:
# 1. Missing OLLAMA_HOST environment variable
# 2. Ollama server offline
# 3. Model not pulled on Ollama server
```

---

## See Also

- [GETTING_STARTED.md](./GETTING_STARTED.md) — Local installation
- [ARCHITECTURE.md](./ARCHITECTURE.md) — System design
- [TESTING.md](./TESTING.md) — Test before deploying
