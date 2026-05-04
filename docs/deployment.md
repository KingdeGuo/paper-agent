# Deployment Guide

Production deployment options for Paper Agent.

---

## 🐳 Docker Compose (Single Server)

For single-server production deployment:

```bash
git clone https://github.com/KingdeGuo/paper-agent.git
cd paper-agent

# Create production environment
cp .env.example .env
# Edit .env with production values (see Configuration Guide)

# Start with production settings
docker-compose -f docker-compose.yml up -d
```

### Production Considerations

1. **Use a reverse proxy (Nginx) in front:**

```nginx
server {
    listen 80;
    server_name papers.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    location /health {
        proxy_pass http://localhost:8000;
    }
}
```

2. **Enable SSL with Let's Encrypt:**
   ```bash
   sudo certbot --nginx -d papers.yourdomain.com
   ```

3. **Configure backups:**
   ```bash
   # Backup PostgreSQL
   docker exec paper-agent-postgres pg_dump -U paper_agent paper_agent > backup_$(date +%Y%m%d).sql

   # Backup data directory
   tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
   ```

---

## ☸️ Kubernetes Deployment

Full Kubernetes manifests are included in `k8s/`:

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets
kubectl apply -f k8s/secrets.yaml

# Deploy infrastructure
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/minio.yaml

# Deploy application
kubectl apply -f k8s/backend-api.yaml
kubectl apply -f k8s/backend-worker.yaml

# Set up ingress
kubectl apply -f k8s/ingress.yaml
```

### Architecture

```
┌──────────────────────────────────────────────┐
│              Ingress Controller               │
│          (TLS termination, routing)           │
└──────────┬───────────────────────┬───────────┘
           │                       │
     ┌─────▼─────┐          ┌─────▼─────┐
     │  API v1   │          │  API v2   │
     │   Pod     │          │   Pod     │
     └─────┬─────┘          └─────┬─────┘
           │                      │
           └──────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │    PostgreSQL         │
          │    (StatefulSet)      │
          └───────────────────────┘
```

### Scaling

```bash
# Scale API replicas
kubectl scale deployment paper-agent-api --replicas=5

# Scale workers
kubectl scale deployment paper-agent-worker --replicas=3

# Auto-scaling (if metrics server is installed)
kubectl autoscale deployment paper-agent-api --min=2 --max=10 --cpu-percent=70
```

### Monitoring

The health endpoint is available at `/health` on each pod. Configure your monitoring system (Prometheus, Datadog, etc.) to watch:

- API response times
- Document processing throughput
- Queue depth
- Error rates

---

## 📊 Resource Requirements

| Deployment | CPU | Memory | Storage |
|------------|-----|--------|---------|
| Development (SQLite) | 2 cores | 4GB RAM | 10GB |
| Production (Single Server) | 4 cores | 8GB RAM | 50GB+ |
| Production (Kubernetes) | 2-10 pods | 4GB/pod | Depends on documents |

### Database Sizing

| Documents | PostgreSQL Storage | Vector DB Storage |
|-----------|-------------------|-------------------|
| 100 | ~50MB | ~100MB |
| 1,000 | ~500MB | ~1GB |
| 10,000 | ~5GB | ~10GB |
| 100,000 | ~50GB | ~100GB |

---

## 🛡️ Security Hardening

1. **Network Isolation:**
   - Place database, Redis, and MinIO on a private network
   - Only expose the frontend and API through the reverse proxy
   - Use Kubernetes NetworkPolicies for pod-level isolation

2. **Secrets Management:**
   - Use Kubernetes Secrets or HashiCorp Vault
   - Never store secrets in environment variables in CI/CD
   - Rotate secrets regularly

3. **Regular Updates:**
   - Keep the Docker base images updated
   - Monitor for security advisories
   - Use automated dependency updates (Dependabot configured)

4. **Backup Strategy:**
   - Daily database backups (retain 30 days)
   - Weekly full backup of all data
   - Test restoration process monthly

---

## 🔄 Upgrade Procedure

```bash
# 1. Backup current data
docker exec paper-agent-postgres pg_dump -U paper_agent paper_agent > pre_upgrade.sql

# 2. Pull latest code
git pull origin main

# 3. Rebuild and restart
docker-compose build --no-cache
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/health

# 5. Run database migrations (if applicable)
docker-compose exec backend alembic upgrade head

# 6. Verify functionality
# - Log in
# - Check document list
# - Run a search
# - Generate a summary
```
