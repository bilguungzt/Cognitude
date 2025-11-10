# Enhanced Frontend - Installation & Deployment Guide

## 📋 Prerequisites

- Node.js 18+ (recommended: 20.x)
- npm or yarn
- Git (for version control)

Check your versions:

```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 9.0.0 or higher
```

## 🚀 Local Development Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install:

- React 19.x
- React Router DOM 7.x
- Tailwind CSS 3.x
- Lucide React (icons)
- Recharts (data visualization)
- TypeScript 5.x
- Vite 7.x (build tool)

### 2. Environment Configuration

Create `.env` file in the `frontend` directory (if not exists):

```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```

For production:

```bash
VITE_API_URL=https://your-api-domain.com
```

### 3. Start Development Server

```bash
npm run dev
```

Server will start at `http://localhost:5173` (or next available port)

### 4. Verify Installation

1. Visit `http://localhost:5173`
2. You should see the enhanced login page
3. Register a new organization
4. Save the API key
5. Log in with the API key
6. You should see the enhanced dashboard

## 🏗️ Build for Production

### 1. Build the Project

```bash
npm run build
```

This creates an optimized production build in `frontend/dist/` directory.

### 2. Preview Production Build Locally

```bash
npm run preview
```

### 3. Build Output

The `dist` folder contains:

```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js     # Main JavaScript bundle
│   ├── index-[hash].css    # Compiled CSS
│   └── [other assets]
└── [other files]
```

## 🌐 Deployment Options

### Option 1: Static Hosting (Vercel, Netlify)

#### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel
```

Or use the Vercel dashboard:

1. Connect your GitHub repo
2. Set build command: `npm run build`
3. Set output directory: `dist`
4. Set environment variable: `VITE_API_URL=https://your-api.com`
5. Deploy!

#### Netlify

```bash
# Install Netlify CLI
npm i -g netlify-cli

# Deploy
cd frontend
netlify deploy --prod --dir=dist
```

Or use the Netlify dashboard:

1. Connect your GitHub repo
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Set environment variable: `VITE_API_URL=https://your-api.com`
5. Deploy!

### Option 2: Traditional Web Server (Nginx, Apache)

#### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /var/www/cognitude-frontend/dist;
    index index.html;

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip compression
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_comp_level 6;

    # Cache static assets
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

#### Apache Configuration (.htaccess)

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteCond %{REQUEST_FILENAME} !-l
  RewriteRule . /index.html [L]
</IfModule>

# Gzip compression
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/javascript application/json
</IfModule>

# Browser caching
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresByType image/jpg "access plus 1 year"
  ExpiresByType image/jpeg "access plus 1 year"
  ExpiresByType image/gif "access plus 1 year"
  ExpiresByType image/png "access plus 1 year"
  ExpiresByType text/css "access plus 1 month"
  ExpiresByType application/javascript "access plus 1 month"
</IfModule>
```

### Option 3: Docker Deployment

Create `frontend/Dockerfile`:

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

Create `frontend/nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
}
```

Build and run:

```bash
cd frontend
docker build -t cognitude-frontend .
docker run -p 80:80 cognitude-frontend
```

### Option 4: Docker Compose (with Backend)

Update your existing `docker-compose.yml`:

```yaml
version: "3.8"

services:
  # Backend service (existing)
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/cognitude
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  # Frontend service (NEW)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    environment:
      - VITE_API_URL=http://backend:8000
    depends_on:
      - backend

  # Database (existing)
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=cognitude
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis (existing)
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Deploy:

```bash
docker-compose up -d
```

## 🔒 Production Best Practices

### 1. Environment Variables

Never commit `.env` files. Use:

- Vercel/Netlify: Dashboard environment variables
- Docker: `.env.production` file (gitignored)
- Traditional: Server environment variables

### 2. Security Headers

Add these headers in your web server config:

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';
```

### 3. HTTPS

Always use HTTPS in production:

- Vercel/Netlify: Automatic SSL
- Traditional: Use Let's Encrypt (certbot)
- Docker: Use nginx-proxy with Let's Encrypt companion

### 4. CORS Configuration

In your backend, ensure CORS is configured for your frontend domain:

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Development
        "https://your-frontend-domain.com",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. Performance Optimization

```bash
# Analyze bundle size
npm run build
npx vite-bundle-visualizer

# Enable compression (gzip/brotli)
# Already configured in nginx/apache examples above

# CDN for static assets (optional)
# Upload /assets/ folder to CDN
# Update imports to use CDN URLs
```

## 🧪 Testing Before Deployment

### 1. Build Test

```bash
npm run build
npm run preview
```

### 2. Checklist

- ✅ Login/register flow works
- ✅ Dashboard loads models
- ✅ Search and filter work
- ✅ Cost dashboard shows charts
- ✅ All navigation links work
- ✅ Mobile menu works
- ✅ Toast notifications appear
- ✅ Modal opens/closes
- ✅ CSV export downloads
- ✅ API calls succeed
- ✅ Error handling works
- ✅ Loading states show

### 3. Browser Testing

Test in:

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile Safari (iOS)
- Chrome Mobile (Android)

## 🔄 Continuous Deployment

### GitHub Actions Example

Create `.github/workflows/deploy-frontend.yml`:

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]
    paths:
      - "frontend/**"

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: "20"

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Build
        working-directory: ./frontend
        run: npm run build
        env:
          VITE_API_URL: ${{ secrets.API_URL }}

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: ./frontend
          vercel-args: "--prod"
```

## 📊 Monitoring

### Add Analytics (Optional)

#### Google Analytics

```typescript
// frontend/src/main.tsx
import ReactGA from "react-ga4";

if (import.meta.env.PROD) {
  ReactGA.initialize("G-XXXXXXXXXX");
}
```

#### Sentry Error Tracking

```bash
npm install @sentry/react
```

```typescript
// frontend/src/main.tsx
import * as Sentry from "@sentry/react";

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: "YOUR_SENTRY_DSN",
    environment: "production",
  });
}
```

## 🐛 Troubleshooting

### Build Fails

```bash
# Clear cache
rm -rf node_modules/.vite
rm -rf node_modules
npm install
npm run build
```

### Blank Page After Deployment

- Check browser console for errors
- Verify VITE_API_URL is set correctly
- Check CORS configuration on backend
- Verify routing is configured (try_files for nginx)

### API Calls Fail

- Check VITE_API_URL environment variable
- Verify CORS headers
- Check backend is accessible from frontend domain
- Check browser network tab for errors

### Assets Not Loading

- Check base URL in vite.config.ts
- Verify assets are in dist/assets/ after build
- Check nginx/apache static file serving

## 📞 Support

If you encounter issues:

1. Check the browser console for errors
2. Review the network tab for API call failures
3. Verify environment variables are set
4. Check backend logs
5. Review deployment logs

## ✅ Deployment Checklist

Before going live:

- [ ] Environment variables configured
- [ ] Backend CORS configured
- [ ] Build succeeds without errors
- [ ] Preview build works locally
- [ ] All features tested
- [ ] Mobile experience tested
- [ ] HTTPS configured
- [ ] Security headers added
- [ ] Analytics configured (optional)
- [ ] Error tracking configured (optional)
- [ ] Monitoring set up
- [ ] DNS configured
- [ ] Backup/rollback plan ready

## 🎉 You're Ready!

Your enhanced Cognitude AI frontend is now deployed and ready to use!

**Quick Links:**

- Development: `http://localhost:5173`
- Production: `https://your-domain.com`
- Documentation: See ENHANCED_FRONTEND_README.md
- Quick Start: See ENHANCED_FRONTEND_QUICKSTART.md
