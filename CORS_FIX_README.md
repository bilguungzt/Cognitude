# CORS Fix for Cognitude API

This document explains how to fix the CORS issue that prevents your frontend (running on `http://localhost:5175`) from registering new organizations at `https://api.cognitude.io/auth/register`.

## Problem Description

When your frontend tries to make a request to the production API, it fails due to CORS (Cross-Origin Resource Sharing) restrictions. This happens because:

1. Your frontend runs on `http://localhost:5175` (different origin from the API)
2. The production API is at `https://api.cognitude.io`
3. The nginx reverse proxy on the production server isn't properly forwarding CORS headers

## Solution

The solution involves updating the nginx configuration on your production server to properly handle CORS headers.

### Files Included

1. `nginx_cors_fix.conf` - The updated nginx configuration file with proper CORS headers
2. `apply_cors_fix.sh` - A script to apply the fix to your production server

### How to Apply the Fix

#### Option 1: Using the Script (Recommended)

1. Upload both files to your production server:
   ```bash
   scp nginx_cors_fix.conf apply_cors_fix.sh root@165.22.158.75:/tmp/
   ```

2. SSH into your production server:
   ```bash
   ssh root@165.22.158.75
   ```

3. Navigate to the directory where you uploaded the files:
   ```bash
   cd /tmp
   ```

4. Make the script executable and run it:
   ```bash
   chmod +x apply_cors_fix.sh
   sudo ./apply_cors_fix.sh
   ```

#### Option 2: Manual Configuration

1. SSH into your production server:
   ```bash
   ssh root@165.22.158.75
   ```

2. Edit the nginx configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/cognitude
   ```

3. Replace the content with the configuration from `nginx_cors_fix.conf`

4. Test and reload nginx:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Configuration Details

The new nginx configuration includes:

- Proper CORS headers for all requests
- Special handling for preflight OPTIONS requests
- SSL configuration for HTTPS
- Automatic redirect from HTTP to HTTPS

### Verification

After applying the fix:

1. Try registering a new organization from your frontend again
2. Check that the browser no longer shows CORS errors
3. Verify that the registration request completes successfully

### Troubleshooting

If you still experience issues:

1. Check nginx error logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. Verify the configuration:
   ```bash
   sudo nginx -t
   ```

3. Check that the site is enabled:
   ```bash
   sudo ls -la /etc/nginx/sites-enabled/
   ```

### SSL Certificate Note

The configuration includes placeholders for SSL certificates. Make sure to update the paths to your actual SSL certificate files:

```nginx
ssl_certificate /path/to/your/certificate.crt;
ssl_certificate_key /path/to/your/private.key;
```

These are typically located at:
- `/etc/letsencrypt/live/api.cognitude.io/fullchain.pem`
- `/etc/letsencrypt/live/api.cognitude.io/privkey.pem`