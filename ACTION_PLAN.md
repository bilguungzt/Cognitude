# DriftGuard MVP - Action Plan to Launch

## Current Status: **70% Complete** ✅

### What's Working:

- ✅ Backend API (FastAPI)
- ✅ Database schema (PostgreSQL)
- ✅ Authentication (API keys)
- ✅ Model registration
- ✅ Prediction logging
- ✅ Drift detection (KS test)
- ✅ Background scheduler
- ✅ Docker deployment
- ✅ Basic tests passing

### What's Missing (Critical Path to First Customer):

- ❌ Frontend Dashboard (React)
- ❌ Notification system (Email/Slack)
- ❌ API documentation
- ❌ Python SDK client
- ❌ Onboarding materials

---

## 🎯 2-Week Sprint to Launch

### **Week 1: Complete Backend & Notifications**

#### Day 1-2: Notifications (HIGH PRIORITY)

**File Created**: `app/services/notifications.py` ✅

**TODO**:

1. Add aiohttp to requirements.txt
2. Update drift_detection.py to call NotificationService
3. Create API endpoint for alert channel configuration:
   ```python
   POST /api/alert-channels
   {
     "channel_type": "email",  # or "slack"
     "configuration": {"email": "user@company.com"}
   }
   ```
4. Test email alerts with Gmail SMTP
5. Test Slack webhooks

**Environment Variables Needed**:

```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=alerts@driftguard.ai
```

#### Day 3: API Documentation

Use FastAPI's automatic docs + add examples:

```python
# app/main.py
app = FastAPI(
    title="DriftGuard AI",
    description="ML Model Monitoring & Drift Detection Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
```

Add response models and examples to all endpoints.

#### Day 4: Python SDK Client

Create `driftguard-client` package:

```python
# driftguard_client/client.py
import requests
from typing import Dict, List, Optional

class DriftGuard:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def register_model(self, name: str, version: str, features: List[Dict]) -> Dict:
        response = requests.post(
            f"{self.base_url}/models/",
            headers=self.headers,
            json={"name": name, "version": version, "features": features}
        )
        response.raise_for_status()
        return response.json()

    def log_predictions(self, model_id: int, predictions: List[Dict]) -> Dict:
        response = requests.post(
            f"{self.base_url}/predictions/models/{model_id}/predictions",
            headers=self.headers,
            json=predictions
        )
        response.raise_for_status()
        return response.json()

    def get_drift_status(self, model_id: int) -> Dict:
        response = requests.get(
            f"{self.base_url}/drift/models/{model_id}/drift/current",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

#### Day 5: Drift History API

Add endpoint to get historical drift scores:

```python
@router.get("/models/{model_id}/drift/history")
async def get_drift_history(
    model_id: int,
    hours: int = 168,  # 7 days default
    api_key: str = Header(),
    db: Session = Depends(get_db)
):
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Query predictions in time windows
    results = []
    current_time = cutoff
    while current_time < datetime.utcnow():
        window_end = current_time + timedelta(hours=1)

        # Calculate drift for this window
        predictions = db.query(Prediction).filter(
            Prediction.model_id == model_id,
            Prediction.time >= current_time,
            Prediction.time < window_end
        ).all()

        if len(predictions) >= 30:
            drift_service = DriftDetectionService(db)
            result = drift_service.calculate_ks_test_drift(model_id)
            results.append({
                "timestamp": current_time.isoformat(),
                "drift_score": result["drift_score"],
                "drift_detected": result["drift_detected"]
            })

        current_time = window_end

    return results
```

---

### **Week 2: Frontend Dashboard**

#### Day 6-7: React Project Setup + Dashboard Layout

```bash
npx create-react-app frontend --template typescript
cd frontend
npm install recharts axios react-router-dom @mui/material @emotion/react @emotion/styled
```

**File Structure**:

```
frontend/
├── src/
│   ├── components/
│   │   ├── ModelCard.tsx
│   │   ├── DriftChart.tsx
│   │   ├── AlertList.tsx
│   │   └── Navbar.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── ModelDetail.tsx
│   │   ├── Settings.tsx
│   │   └── Setup.tsx
│   ├── services/
│   │   └── api.ts
│   └── App.tsx
```

#### Day 8: Model Dashboard Page

**Priority**: Show all models with current drift status

```typescript
// src/pages/Dashboard.tsx
export const Dashboard: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);

  useEffect(() => {
    api.getModels().then(setModels);
  }, []);

  return (
    <Grid container spacing={3}>
      {models.map((model) => (
        <Grid item xs={12} md={6} lg={4} key={model.id}>
          <ModelCard model={model} />
        </Grid>
      ))}
    </Grid>
  );
};
```

#### Day 9: Model Detail Page with Chart

Use Recharts for drift visualization:

```typescript
<LineChart data={driftHistory}>
  <XAxis dataKey="timestamp" />
  <YAxis domain={[0, 1]} />
  <Line type="monotone" dataKey="drift_score" stroke="#8884d8" />
  <ReferenceLine y={0.5} stroke="red" strokeDasharray="3 3" />
</LineChart>
```

#### Day 10: Settings & Alert Configuration

- Email configuration form
- Slack webhook configuration
- Test alert button

#### Day 11: Setup/Onboarding Page

- Copy-paste code examples
- Quick start guide
- API key display

#### Day 12: Polish & Deploy

- Add loading states
- Error handling
- Deploy frontend to Vercel/Netlify
- Deploy backend to DigitalOcean/AWS

---

## 📋 Pre-Launch Checklist

### Backend

- [ ] All API endpoints documented
- [ ] Email alerts working
- [ ] Slack alerts working
- [ ] Background scheduler running
- [ ] Database migrations tested
- [ ] Docker deployment working
- [ ] Environment variables documented

### Frontend

- [ ] Dashboard shows all models
- [ ] Drift charts render correctly
- [ ] Alert configuration saves
- [ ] Setup page has copy-paste examples
- [ ] Mobile responsive
- [ ] Loading states added
- [ ] Error handling added

### Infrastructure

- [ ] SSL certificate configured
- [ ] Domain name pointed to server
- [ ] Database backups configured
- [ ] Monitoring/logging setup
- [ ] Health check endpoint

### Documentation

- [ ] README with setup instructions
- [ ] API documentation published
- [ ] Python SDK published to PyPI
- [ ] Example integration code
- [ ] Troubleshooting guide

### Customer Acquisition

- [ ] Landing page created
- [ ] Demo video recorded
- [ ] Pricing page
- [ ] Contact form
- [ ] First customer outreach list

---

## 🚀 Launch Strategy

### Week 1: Soft Launch

- Deploy to production
- Test with 2-3 beta users
- Fix critical bugs
- Gather feedback

### Week 2: Public Launch

- Post on Product Hunt
- Share on Twitter/LinkedIn
- Email potential customers
- Demo to ML engineering teams

### Target First Customer

- **Industry**: Fintech, E-commerce, or SaaS with ML models
- **Team Size**: 5-15 engineers
- **Models in Production**: 3-10
- **Pain Point**: Manual drift monitoring or no monitoring
- **Price Point**: $1,000/month (up to 5 models)

---

## 💰 Pricing (MVP)

| Tier         | Price     | Models    | Predictions/month |
| ------------ | --------- | --------- | ----------------- |
| Starter      | $500/mo   | 3         | 1M                |
| Professional | $1,000/mo | 10        | 5M                |
| Enterprise   | $2,500/mo | Unlimited | 20M               |

---

## 🎯 Success Metrics

### Week 1

- [ ] 5 beta signups
- [ ] 100 models registered
- [ ] 10K predictions logged
- [ ] 0 critical bugs

### Week 2

- [ ] 1 paying customer ($1K/mo)
- [ ] 10 active users
- [ ] 50 models monitored
- [ ] 100K predictions logged

### Month 1

- [ ] 3 paying customers ($3K MRR)
- [ ] 30 active users
- [ ] 95% uptime
- [ ] < 5 support tickets/week

---

## Next Immediate Actions (TODAY):

1. ✅ **Add aiohttp to requirements.txt**
2. ✅ **Wire NotificationService into drift_detection.py**
3. **Create alert channel configuration endpoint**
4. **Test email alerts end-to-end**
5. **Start React frontend setup**

Would you like me to implement any of these next steps?
