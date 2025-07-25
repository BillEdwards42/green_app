# Cloud Deployment Guide for Green Moment Backend

## Overview
This guide covers deploying the Green Moment backend to various cloud platforms.

## Option 1: Railway (Recommended for Quick Start)

Railway provides the easiest deployment with automatic PostgreSQL and Redis.

### Steps:
1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and Initialize**
   ```bash
   railway login
   railway init
   ```

3. **Add Services**
   ```bash
   # In Railway dashboard, add:
   # - PostgreSQL
   # - Redis
   # These are automatically provisioned
   ```

4. **Deploy**
   ```bash
   railway up
   ```

5. **Set Environment Variables**
   In Railway dashboard, add:
   - `SECRET_KEY` (generate a secure random string)
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
   - Other variables from `.env.example`

### Railway Configuration File
Create `railway.toml`:
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/v1/docs"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

## Option 2: Google Cloud Platform (GCP)

### Prerequisites:
- Google Cloud account
- `gcloud` CLI installed
- Project created in GCP Console

### Steps:

1. **Configure gcloud**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Create Cloud SQL Instance**
   ```bash
   # Create PostgreSQL instance
   gcloud sql instances create green-moment-db \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=us-central1
   
   # Create database
   gcloud sql databases create green_moment \
     --instance=green-moment-db
   
   # Set password
   gcloud sql users set-password postgres \
     --instance=green-moment-db \
     --password=YOUR_PASSWORD
   ```

3. **Create Memorystore Redis**
   ```bash
   gcloud redis instances create green-moment-redis \
     --size=1 \
     --region=us-central1 \
     --redis-version=redis_6_x
   ```

4. **Build and Push Container**
   ```bash
   # Enable required APIs
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   
   # Build and push to Container Registry
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/green-moment-api
   ```

5. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy green-moment-api \
     --image gcr.io/YOUR_PROJECT_ID/green-moment-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --add-cloudsql-instances YOUR_PROJECT_ID:us-central1:green-moment-db \
     --set-env-vars="DATABASE_URL=postgresql://postgres:PASSWORD@/green_moment?host=/cloudsql/YOUR_PROJECT_ID:us-central1:green-moment-db"
   ```

### Cloud Run Configuration
Create `app.yaml` for more control:
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: green-moment-api
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cloudsql-instances: YOUR_PROJECT_ID:us-central1:green-moment-db
        run.googleapis.com/cpu-throttling: "false"
    spec:
      containers:
      - image: gcr.io/YOUR_PROJECT_ID/green-moment-api
        resources:
          limits:
            memory: 512Mi
            cpu: 1
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-url
              key: latest
```

## Option 3: AWS (ECS with Fargate)

### Prerequisites:
- AWS account
- AWS CLI configured
- Docker installed

### Steps:

1. **Create RDS PostgreSQL**
   ```bash
   aws rds create-db-instance \
     --db-instance-identifier green-moment-db \
     --db-instance-class db.t3.micro \
     --engine postgres \
     --engine-version 15 \
     --master-username postgres \
     --master-user-password YOUR_PASSWORD \
     --allocated-storage 20
   ```

2. **Create ElastiCache Redis**
   ```bash
   aws elasticache create-cache-cluster \
     --cache-cluster-id green-moment-redis \
     --engine redis \
     --cache-node-type cache.t3.micro \
     --num-cache-nodes 1
   ```

3. **Push to ECR**
   ```bash
   # Create repository
   aws ecr create-repository --repository-name green-moment-api
   
   # Get login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   
   # Build and push
   docker build -t green-moment-api .
   docker tag green-moment-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/green-moment-api:latest
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/green-moment-api:latest
   ```

4. **Create ECS Task Definition**
   Create `task-definition.json`:
   ```json
   {
     "family": "green-moment-api",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "containerDefinitions": [{
       "name": "api",
       "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/green-moment-api:latest",
       "portMappings": [{
         "containerPort": 8000,
         "protocol": "tcp"
       }],
       "environment": [
         {"name": "DATABASE_URL", "value": "postgresql://..."},
         {"name": "REDIS_URL", "value": "redis://..."}
       ]
     }]
   }
   ```

5. **Deploy to Fargate**
   ```bash
   # Create cluster
   aws ecs create-cluster --cluster-name green-moment
   
   # Register task definition
   aws ecs register-task-definition --cli-input-json file://task-definition.json
   
   # Create service
   aws ecs create-service \
     --cluster green-moment \
     --service-name api \
     --task-definition green-moment-api:1 \
     --desired-count 1 \
     --launch-type FARGATE
   ```

## Post-Deployment Steps

### 1. Update Flutter App
Update `lib/config/api_config.dart`:
```dart
static const String productionUrl = 'https://your-deployed-url.com/api/v1';
```

### 2. Set Up Domain (Optional)
- Point your domain to the deployed service
- Configure SSL certificate (usually automatic)

### 3. Set Up Monitoring
- Enable logging in your cloud provider
- Set up alerts for errors
- Monitor API response times

### 4. Database Migrations
Run migrations after deployment:
```bash
# Railway
railway run alembic upgrade head

# GCP Cloud Run
gcloud run jobs create migrate-db \
  --image gcr.io/YOUR_PROJECT_ID/green-moment-api \
  --command alembic,upgrade,head

# AWS ECS
# Run as a one-time task with the migration command
```

### 5. Configure Background Jobs
For Celery workers:
- Railway: Add another service with celery command
- GCP: Deploy separate Cloud Run service for Celery
- AWS: Create additional ECS service for Celery

## Environment Variables Checklist

Essential variables for production:
- [ ] `SECRET_KEY` - Generate secure random string
- [ ] `DATABASE_URL` - Production database connection
- [ ] `REDIS_URL` - Production Redis connection
- [ ] `GOOGLE_CLIENT_ID` - From Google Console
- [ ] `GOOGLE_CLIENT_SECRET` - From Google Console
- [ ] `ENVIRONMENT` - Set to "production"
- [ ] `DEBUG` - Set to "False"
- [ ] `BACKEND_CORS_ORIGINS` - Your Flutter app domains

## Security Checklist

- [ ] Use environment variables, not hardcoded secrets
- [ ] Enable HTTPS only
- [ ] Set up database backups
- [ ] Configure firewall rules
- [ ] Enable cloud provider security features
- [ ] Rotate secrets regularly
- [ ] Monitor for suspicious activity

## Cost Optimization

### Railway
- ~$5-20/month for small apps
- Automatic scaling

### GCP
- Cloud Run: Pay per request
- Cloud SQL: ~$10/month for db-f1-micro
- Memorystore: ~$15/month minimum

### AWS
- Fargate: ~$10-30/month
- RDS: ~$15/month for t3.micro
- ElastiCache: ~$15/month

## Troubleshooting

### Database Connection Issues
- Check security groups/firewall rules
- Verify connection string format
- Test with cloud provider's connection tools

### Application Errors
- Check logs in cloud console
- Verify all environment variables are set
- Test endpoints with curl from cloud shell

### Performance Issues
- Scale up instance sizes
- Add caching
- Optimize database queries
- Use CDN for static assets