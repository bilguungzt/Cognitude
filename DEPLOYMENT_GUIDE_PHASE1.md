# 🚀 Phase 1 Deployment Guide

**Status**: Ready for Production  
**Date**: November 10, 2025  
**Target Server**: 165.22.158.75:8000

---

## 📋 Pre-Deployment Checklist

### ✅ Code Completion

- [x] Phase 1.1: Redis Caching
- [x] Phase 1.2: Smart Routing
- [x] Phase 1.3: Enhanced Analytics
- [x] Phase 1.4: Alert System
- [x] Phase 1.5: Rate Limiting
- [ ] Integration testing completed
- [ ] All test suites passing

### ✅ Dependencies

- [ ] Python 3.11+ installed
- [ ] Docker & Docker Compose installed
- [ ] PostgreSQL 15+ with TimescaleDB
- [ ] Redis 7+ running
- [ ] All pip dependencies installed (`requirements.txt`)

### ✅ Configuration

- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] LLM provider API keys added
- [ ] SMTP credentials for email alerts (optional)
- [ ] Slack webhook URLs configured (optional)

### ✅ Testing

- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Load testing completed
- [ ] Security review completed

---

## 🔧 Local Testing (Pre-Deployment)

### Step 1: Run Integration Tests

```bash
# 1. Ensure server is running
docker-compose up -d

# 2. Check health
curl http://localhost:8000/health

# 3. Run integration test suite
python test_phase1_integration.py
```

**Expected Output**: All tests passing (or minor failures due to provider config)

### Step 2: Run Individual Feature Tests

```bash
# Test each phase individually
python test_smart_routing.py      # Phase 1.2
python test_analytics.py          # Phase 1.3
python test_alerts.py             # Phase 1.4
python test_rate_limits.py        # Phase 1.5
```

### Step 3: Manual Smoke Tests

```bash
# 1. Create organization
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestOrg",
    "email": "test@example.com",
    "password": "secure123"
  }'

# Save the API key from response

# 2. Configure OpenAI provider
curl -X POST http://localhost:8000/providers/config \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-your-openai-key",
    "enabled": true
  }'

# 3. Test proxy endpoint
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'

# 4. Check rate limit headers
curl -I -X POST http://localhost:8000/v1/chat/completions \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "test"}]
  }' | grep "X-RateLimit"

# 5. Check analytics
curl http://localhost:8000/analytics/usage \
  -H "X-API-Key: YOUR_API_KEY"

# 6. Check recommendations
curl http://localhost:8000/analytics/recommendations \
  -H "X-API-Key: YOUR_API_KEY"

# 7. Check rate limits
curl http://localhost:8000/rate-limits/usage \
  -H "X-API-Key: YOUR_API_KEY"
```

---

## 🚀 Production Deployment

### Step 1: Backup Current System

```bash
# SSH to server
ssh root@165.22.158.75

# Backup database
cd /opt/cognitude
docker-compose exec db pg_dump -U cognitude cognitude > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup current code
tar -czf cognitude_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/cognitude

# Store backups
mv *.sql *.tar.gz /opt/backups/
```

### Step 2: Deploy New Code

```bash
# Method 1: Git pull (recommended)
cd /opt/cognitude
git pull origin main

# Method 2: Manual upload (if using local dev)
# From local machine:
rsync -avz --exclude 'venv' --exclude '__pycache__' \
  /Users/billy/Documents/Projects/cognitude_mvp/ \
  root@165.22.158.75:/opt/cognitude/
```

### Step 3: Install New Dependencies

```bash
cd /opt/cognitude

# Update requirements
pip install -r requirements.txt

# Or rebuild Docker image
docker-compose build api
```

### Step 4: Run Database Migrations

```bash
# Create migration for new tables
alembic revision --autogenerate -m "Add Phase 1 tables (rate_limit_configs, alert_configs, alert_channels)"

# Review migration
cat alembic/versions/[latest_version].py

# Apply migration
alembic upgrade head

# Verify tables created
docker-compose exec db psql -U cognitude -c "\dt"
```

**Expected New Tables**:

- `rate_limit_configs`
- `alert_configs`
- `alert_channels`

### Step 5: Update Environment Variables

```bash
# Edit .env file
nano .env

# Add/update these variables:
REDIS_HOST=redis
REDIS_PORT=6379

# SMTP for email alerts (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Save and exit (Ctrl+X, Y, Enter)
```

### Step 6: Restart Services

```bash
# Restart all services
docker-compose down
docker-compose up -d

# Or restart specific services
docker-compose restart api
docker-compose restart redis

# Check logs
docker-compose logs -f api
docker-compose logs redis
```

### Step 7: Verify Deployment

```bash
# 1. Health check
curl http://165.22.158.75:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "Cognitude LLM Proxy",
#   "version": "1.0.0",
#   "redis": {"status": "connected", "keys": 0}
# }

# 2. Check API docs
curl http://165.22.158.75:8000/docs
# Should return HTML with OpenAPI docs

# 3. Test new endpoints
curl http://165.22.158.75:8000/rate-limits/config \
  -H "X-API-Key: YOUR_API_KEY"

curl http://165.22.158.75:8000/analytics/recommendations \
  -H "X-API-Key: YOUR_API_KEY"
```

### Step 8: Run Production Tests

```bash
# From your local machine, test production server
export BASE_URL=http://165.22.158.75:8000
export API_KEY=your-production-key

# Run integration tests against production
python test_phase1_integration.py
```

---

## 📊 Post-Deployment Monitoring

### Metrics to Watch (First 24 Hours)

**Performance**:

- [ ] Average response latency (<100ms)
- [ ] Cache hit rate (>50% after 1 hour)
- [ ] Redis memory usage (<256MB)
- [ ] Database connections (<20)

**Functionality**:

- [ ] Successful LLM requests (>95%)
- [ ] Cache hits working correctly
- [ ] Smart routing classifications accurate
- [ ] Recommendations generating correctly
- [ ] Rate limits enforcing properly

**Errors**:

- [ ] No 5xx errors (server errors)
- [ ] 429 rate limit responses (expected, monitor rate)
- [ ] Background jobs running (scheduler logs)
- [ ] Alert delivery success (if configured)

### Monitoring Commands

```bash
# Watch logs in real-time
docker-compose logs -f --tail=100 api

# Check Redis stats
docker-compose exec redis redis-cli info stats

# Check database connections
docker-compose exec db psql -U cognitude -c "SELECT count(*) FROM pg_stat_activity;"

# Check recent requests
docker-compose exec db psql -U cognitude -c \
  "SELECT count(*), model, cached, AVG(latency_ms)
   FROM llm_requests
   WHERE timestamp > NOW() - INTERVAL '1 hour'
   GROUP BY model, cached;"

# Check rate limit usage
curl http://165.22.158.75:8000/rate-limits/usage \
  -H "X-API-Key: YOUR_API_KEY"

# Check cache stats
curl http://165.22.158.75:8000/cache/stats \
  -H "X-API-Key: YOUR_API_KEY"
```

### Set Up Monitoring Dashboard

```bash
# Option 1: Grafana + Prometheus (recommended)
# See: monitoring/README.md (to be created)

# Option 2: Simple log monitoring
# Install logwatch or similar

# Option 3: API-based monitoring
# Create cron job to check health every 5 minutes
crontab -e

# Add:
# */5 * * * * curl -f http://localhost:8000/health || echo "Cognitude down!" | mail -s "Alert" admin@example.com
```

---

## 🔧 Configuration Guide

### 1. Configure LLM Providers

```bash
# OpenAI
curl -X POST http://165.22.158.75:8000/providers/config \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-your-openai-key",
    "enabled": true
  }'

# Anthropic (optional)
curl -X POST http://165.22.158.75:8000/providers/config \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "anthropic",
    "api_key": "sk-ant-your-key",
    "enabled": true
  }'
```

### 2. Configure Alert Channels

```bash
# Slack channel
curl -X POST http://165.22.158.75:8000/alerts/channels \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "slack",
    "configuration": {
      "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    }
  }'

# Email channel
curl -X POST http://165.22.158.75:8000/alerts/channels \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_type": "email",
    "configuration": {
      "email": "alerts@your-company.com"
    }
  }'
```

### 3. Configure Cost Alerts

```bash
# Daily cost alert ($50 threshold)
curl -X POST http://165.22.158.75:8000/alerts/configs \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "daily_cost",
    "threshold_usd": 50.00
  }'

# Monthly cost alert ($1000 threshold)
curl -X POST http://165.22.158.75:8000/alerts/configs \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "alert_type": "monthly_cost",
    "threshold_usd": 1000.00
  }'
```

### 4. Configure Rate Limits (Optional)

```bash
# Update rate limits for your tier
curl -X PUT http://165.22.158.75:8000/rate-limits/config \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "requests_per_minute": 200,
    "requests_per_hour": 6000,
    "requests_per_day": 100000,
    "enabled": true
  }'
```

---

## 🔥 Rollback Procedure (If Needed)

### Quick Rollback

```bash
# 1. Stop services
docker-compose down

# 2. Restore previous code
cd /opt/backups
tar -xzf cognitude_backup_YYYYMMDD_HHMMSS.tar.gz -C /opt/

# 3. Rollback database (if needed)
docker-compose up -d db
docker-compose exec db psql -U cognitude < backup_YYYYMMDD_HHMMSS.sql

# 4. Restart services
docker-compose up -d

# 5. Verify
curl http://165.22.158.75:8000/health
```

### Database-Only Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Or rollback to specific version
alembic downgrade abc123

# Verify
alembic current
```

---

## 📝 Post-Deployment Tasks

### Day 1

- [ ] Monitor logs for errors
- [ ] Verify cache hit rate increasing
- [ ] Check rate limit is enforcing
- [ ] Test alert delivery (create test alert)
- [ ] Verify analytics generating recommendations

### Week 1

- [ ] Review cost savings vs baseline
- [ ] Analyze smart routing effectiveness
- [ ] Review alert thresholds (adjust if needed)
- [ ] Check rate limit appropriateness
- [ ] Gather user feedback

### Month 1

- [ ] Full performance review
- [ ] Cost savings analysis
- [ ] User satisfaction survey
- [ ] Plan Phase 2 enhancements
- [ ] Document lessons learned

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: Redis connection failed

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

**Issue**: Rate limiting not working

```bash
# Check Redis connection
curl http://165.22.158.75:8000/health

# Check rate limit config
curl http://165.22.158.75:8000/rate-limits/config \
  -H "X-API-Key: YOUR_API_KEY"

# Reset rate limits (admin)
curl -X POST http://165.22.158.75:8000/rate-limits/reset \
  -H "X-API-Key: YOUR_API_KEY"
```

**Issue**: Alerts not sending

```bash
# Check SMTP configuration
docker-compose exec api env | grep SMTP

# Test alert channel
curl -X POST http://165.22.158.75:8000/alerts/test/CHANNEL_ID \
  -H "X-API-Key: YOUR_API_KEY"

# Check scheduler logs
docker-compose logs api | grep "Cost alert"
```

**Issue**: Cache not working

```bash
# Check Redis keys
docker-compose exec redis redis-cli keys "*"

# Check cache stats
curl http://165.22.158.75:8000/cache/stats \
  -H "X-API-Key: YOUR_API_KEY"

# Clear cache
curl -X DELETE http://165.22.158.75:8000/cache/clear \
  -H "X-API-Key: YOUR_API_KEY"
```

**Issue**: Smart routing errors

```bash
# Test analyze endpoint
curl -X POST http://165.22.158.75:8000/v1/smart/analyze \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "test"}],
    "mode": "cost"
  }'

# Check smart routing info
curl http://165.22.158.75:8000/v1/smart/info \
  -H "X-API-Key: YOUR_API_KEY"
```

---

## 📞 Support

**Emergency Contacts**:

- Server Admin: [your-email]
- Database Admin: [db-admin]
- DevOps Team: [devops-slack]

**Documentation**:

- API Docs: http://165.22.158.75:8000/docs
- Phase 1 Summary: `PHASE_1_COMPLETE.md`
- Individual Feature Docs: `PHASE_1_[1-5]_*.md`

**Logs Location**:

- API Logs: `docker-compose logs api`
- Redis Logs: `docker-compose logs redis`
- Database Logs: `docker-compose logs db`
- Nginx Logs: `/var/log/nginx/` (if applicable)

---

## ✅ Deployment Sign-Off

- [ ] All pre-deployment checks completed
- [ ] Integration tests passing
- [ ] Production deployment successful
- [ ] Post-deployment monitoring active
- [ ] Configuration completed
- [ ] Team notified
- [ ] Documentation updated

**Deployed By**: ******\_******  
**Date**: ******\_******  
**Sign-Off**: ******\_******

---

**Status**: 📋 Ready for Deployment

Next: Run `python test_phase1_integration.py` locally to verify all features before production deployment.
