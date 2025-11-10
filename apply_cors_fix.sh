#!/bin/bash

# Script to apply CORS fix to the production nginx configuration
# Run this script on your production server as root or with sudo

echo "Applying CORS fix to nginx configuration..."

# Backup existing configuration
if [ -f /etc/nginx/sites-available/cognitude ]; then
    echo "Backing up existing configuration..."
    sudo cp /etc/nginx/sites-available/cognitude /etc/nginx/sites-available/cognitude.backup.$(date +%Y%m%d_%H%M%S)
fi

# Copy the new configuration
sudo cp nginx_cors_fix.conf /etc/nginx/sites-available/cognitude

# Create symbolic link if it doesn't exist
if [ ! -L /etc/nginx/sites-enabled/cognitude ]; then
    sudo ln -s /etc/nginx/sites-available/cognitude /etc/nginx/sites-enabled/
fi

# Test nginx configuration
echo "Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "Configuration test passed. Reloading nginx..."
    sudo systemctl reload nginx
    echo "Nginx reloaded successfully!"
    echo "CORS fix applied successfully!"
else
    echo "Configuration test failed. Reverting to backup..."
    if [ -f /etc/nginx/sites-available/cognitude.backup.$(date +%Y%m%d_%H%M%S) ]; then
        sudo cp /etc/nginx/sites-available/cognitude.backup.$(date +%Y%m%d_%H%M%S) /etc/nginx/sites-available/cognitude
        sudo nginx -t
        sudo systemctl reload nginx
    fi
    echo "Error: Configuration test failed. Please check your nginx configuration."
    exit 1
fi

echo "CORS fix applied successfully!"
echo "You should now be able to register new organizations from your frontend."