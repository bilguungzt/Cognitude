import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

import time
from .api import auth, proxy, analytics, providers, cache, smart_routing, alerts, rate_limits, monitoring, dashboard, schemas, public_benchmarks, metrics
from .api.monitoring import request_count, request_latency
from .database import Base, engine
from .services.background_tasks import scheduler
from .services.tracing import setup_tracing, instrument_app, tracer
from .limiter import limiter
from .config import get_settings

settings = get_settings()
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(),
        ],
        traces_sample_rate=0.2,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-run migrations on startup
    import subprocess
    import sys
    
    try:
        # Run Alembic migrations
        print("Running database migrations...")
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
            print(result.stdout)
        else:
            print("❌ Database migrations failed:")
            print(result.stderr)
            # Don't raise exception - allow app to start even if migrations fail
            # This is important for development and first-time setup
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        print("Continuing with application startup...")
    
    scheduler.start()
    yield
    scheduler.shutdown()


# Initialize tracing
tracer = setup_tracing(app_name="cognitude-api", environment=settings.ENVIRONMENT or "development")

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

# Instrument the app with OpenTelemetry
instrument_app(app)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return _rate_limit_exceeded_handler(request, exc)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def track_metrics(request: Request, call_next):
    # Skip metrics for health checks
    if request.url.path in ["/", "/health"]:
        return await call_next(request)
    
    # Start OpenTelemetry span
    with tracer.start_as_current_span("http_request") as span:
        # Add request attributes
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.target", request.url.path)
        span.set_attribute("http.host", request.url.hostname or "unknown")
        span.set_attribute("http.scheme", request.url.scheme)
        span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
        
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Add response attributes
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_time_ms", process_time * 1000)
            
            # Update Prometheus metrics
            endpoint = request.url.path
            status_code = response.status_code
            
            request_count.labels(method=request.method, endpoint=endpoint, status=status_code).inc()
            request_latency.labels(method=request.method, endpoint=endpoint).observe(process_time)
            
            # Set span status based on response
            if status_code >= 400:
                span.set_status(Status(StatusCode.ERROR, f"HTTP {status_code}"))
            else:
                span.set_status(Status(StatusCode.OK))
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            
            # Record exception in span
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            
            # Update error metrics
            request_count.labels(method=request.method, endpoint=request.url.path, status=500).inc()
            request_latency.labels(method=request.method, endpoint=request.url.path).observe(process_time)
            raise

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
# Core functionality
app.include_router(proxy.router, tags=["proxy"])
app.include_router(providers.router, tags=["providers"])

# Monitoring & Analytics
app.include_router(monitoring.router, tags=["monitoring"])
app.include_router(analytics.router, tags=["analytics"])

# Configuration
app.include_router(rate_limits.router, tags=["rate-limits"])
app.include_router(alerts.router, tags=["alerts"])
app.include_router(smart_routing.router)  # Smart routing endpoints
app.include_router(cache.router)  # Uses /cache prefix from router
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(schemas.router, prefix="/api/schemas", tags=["schemas"])
app.include_router(public_benchmarks.router)
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def read_root():
    return {
        "message": "Cognitude LLM Proxy",
        "version": "1.0.0",
        "docs": "/docs"
    }
