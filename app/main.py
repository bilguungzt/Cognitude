from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import auth, proxy, analytics, providers, cache, smart_routing, alerts, rate_limits
from .database import Base, engine
from .services.background_tasks import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Note: Run 'alembic upgrade head' to apply database migrations
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Cognitude LLM Proxy",
    description="""
## LLM Proxy with Intelligent Caching & Multi-Provider Routing

Cognitude is an OpenAI-compatible LLM proxy that provides intelligent caching, multi-provider routing, and comprehensive cost analytics.

### ✨ Key Features

* **🔄 OpenAI Compatible**: Drop-in replacement for OpenAI SDK
* **💾 Intelligent Caching**: 30-70% cost savings through response caching
* **🌐 Multi-Provider**: Support for OpenAI, Anthropic, Mistral, Groq
* **💰 Cost Tracking**: Accurate per-request cost calculation
* **📊 Analytics**: Comprehensive usage metrics and insights
* **🔐 Multi-Tenant**: Secure API key-based organization isolation

### 🚀 Quick Start

```python
from openai import OpenAI

# Use Cognitude instead of OpenAI directly
client = OpenAI(
    api_key="your-cognitude-api-key",
    base_url="http://your-server:8000/v1"
)

# Same OpenAI code works!
response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### 📖 API Endpoints

* **Chat Completions**: `POST /v1/chat/completions` - OpenAI-compatible LLM endpoint
* **List Models**: `GET /v1/models` - Available models based on your providers
* **Analytics**: `GET /analytics/usage` - Usage metrics and cost breakdown
* **Providers**: `/providers/*` - Manage LLM provider configurations
* **Cache**: `/cache/*` - Cache management and statistics

### 🔐 Authentication

All endpoints require an API key in the `X-API-Key` header:

```bash
curl -X POST http://your-server:8000/v1/chat/completions \\
  -H "X-API-Key: your-api-key" \\
  -H "Content-Type: application/json" \\
  -d '{"model": "gpt-3.5-turbo", "messages": [...]}'
```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Cognitude Support",
        "url": "https://cognitude.io/support",
        "email": "support@cognitude.io"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for simplicity
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(proxy.router)  # No prefix - uses /v1 from router
app.include_router(providers.router)  # Uses /providers prefix from router
app.include_router(cache.router)  # Uses /cache prefix from router
app.include_router(analytics.router)  # Uses /analytics prefix from router
app.include_router(smart_routing.router)  # Smart routing endpoints
app.include_router(alerts.router)  # Alert management endpoints
app.include_router(rate_limits.router)  # Rate limiting configuration

@app.get("/")
def read_root():
    return {
        "message": "Cognitude LLM Proxy",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", tags=["system"])
def health_check():
    """
    Health check endpoint for monitoring and load balancers
    """
    from .services.redis_cache import redis_cache
    
    redis_status = redis_cache.health_check()
    
    return {
        "status": "healthy",
        "service": "Cognitude LLM Proxy",
        "version": "1.0.0",
        "redis": redis_status
    }
