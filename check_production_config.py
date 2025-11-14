#!/usr/bin/env python3
"""
Script to check production configuration on Digital Ocean server.
This script will SSH into the production server and check the .env file.
"""

import subprocess
import sys
import os

def run_ssh_command(host, command):
    """Run a command on remote server via SSH."""
    try:
        ssh_cmd = f"ssh root@{host} '{command}'"
        result = subprocess.run(ssh_cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def check_production_env():
    """Check the production .env file."""
    print("=== PRODUCTION ENVIRONMENT CHECK ===")
    
    # Production server details
    host = "165.22.158.75"
    
    print(f"Connecting to production server: {host}")
    print("=" * 50)
    
    # Check if we can connect
    print("1. Testing SSH connectivity...")
    returncode, stdout, stderr = run_ssh_command(host, "echo 'Connection successful'")
    
    if returncode != 0:
        print(f"   ✗ Cannot connect to production server")
        print(f"   Error: {stderr}")
        print("\nPlease ensure:")
        print("   - You have SSH access to the server")
        print("   - Your SSH key is configured")
        print("   - The server is running and accessible")
        return False
    
    print("   ✓ SSH connection successful")
    
    # Check if .env file exists
    print("\n2. Checking for .env file...")
    returncode, stdout, stderr = run_ssh_command(host, "ls -la /root/cognitude_mvp/.env")
    
    if returncode != 0:
        print(f"   ✗ .env file not found at /root/cognitude_mvp/.env")
        print(f"   Error: {stderr}")
        
        # Check current directory
        returncode, stdout, stderr = run_ssh_command(host, "pwd && ls -la .env")
        if returncode == 0:
            print(f"   Found .env in current directory:")
            print(f"   {stdout}")
        else:
            print("   ✗ No .env file found in current directory either")
            return False
    else:
        print("   ✓ .env file found")
        print(f"   {stdout}")
    
    # Read the .env file
    print("\n3. Reading production .env configuration...")
    returncode, stdout, stderr = run_ssh_command(host, "cat /root/cognitude_mvp/.env")
    
    if returncode != 0:
        print(f"   ✗ Cannot read .env file")
        print(f"   Error: {stderr}")
        return False
    
    print("   ✓ Successfully read .env file")
    print("\n" + "=" * 50)
    print("PRODUCTION .ENV CONTENT:")
    print("=" * 50)
    
    # Parse and display the .env content (masking secrets)
    lines = stdout.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if 'DATABASE_URL' in line:
                # Extract and mask the database URL
                if '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"\'')
                    if '@' in value:
                        # Mask password
                        masked = value.split('@')[0].split('://')[0] + '://***:***@' + value.split('@')[1]
                        print(f"{key}={masked}")
                    else:
                        print(f"{key}={value}")
                else:
                    print(line)
            elif any(secret in line for secret in ['KEY', 'PASSWORD', 'TOKEN', 'SECRET']):
                # Mask other secrets
                if '=' in line:
                    key, value = line.split('=', 1)
                    print(f"{key}=***")
                else:
                    print(line)
            else:
                print(line)
        elif line.startswith('#'):
            print(line)
    
    # Check specifically for DATABASE_URL configuration
    print("\n" + "=" * 50)
    print("DATABASE CONFIGURATION ANALYSIS:")
    print("=" * 50)
    
    for line in lines:
        if 'DATABASE_URL' in line and '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            value = value.strip('"\'')
            
            if 'supabase.co' in value:
                print("✓ Production is using SUPABASE")
                print(f"  Database: Supabase PostgreSQL")
                print(f"  Host: {value.split('@')[1].split(':')[0] if '@' in value else 'Unknown'}")
            elif 'localhost' in value or '127.0.0.1' in value:
                print("⚠ Production is using LOCAL PostgreSQL")
                print(f"  Database: Local PostgreSQL")
                print(f"  Host: {value.split('@')[1].split(':')[0] if '@' in value else 'Unknown'}")
            elif 'db' in value and ':' not in value.split('@')[1]:
                print("⚠ Production is using DOCKER PostgreSQL")
                print(f"  Database: Docker PostgreSQL")
                print(f"  Host: {value.split('@')[1].split('/')[0] if '@' in value else 'Unknown'}")
            else:
                print("? Unknown database configuration")
                print(f"  Raw URL: {value}")
            
            break
    else:
        print("✗ DATABASE_URL not found in .env file")
    
    # Check Docker containers
    print("\n4. Checking Docker containers...")
    returncode, stdout, stderr = run_ssh_command(host, "docker ps --format 'table {{.Names}}\\t{{.Ports}}\\t{{.Status}}'")
    
    if returncode == 0:
        print("   ✓ Docker containers:")
        for line in stdout.strip().split('\n'):
            if 'db' in line.lower() or 'postgres' in line.lower():
                print(f"   ⚠ {line} - PostgreSQL container detected!")
            else:
                print(f"   {line}")
    else:
        print(f"   Cannot check Docker: {stderr}")
    
    return True

def main():
    """Main function."""
    print("Checking production configuration on Digital Ocean...")
    print("This will SSH into 165.22.158.75 and examine the .env file")
    print()
    
    success = check_production_env()
    
    if success:
        print("\n" + "=" * 50)
        print("CHECK COMPLETE")
        print("=" * 50)
        print("\nNext steps:")
        print("1. If production is using local PostgreSQL, update the .env file")
        print("2. Replace DATABASE_URL with Supabase connection string")
        print("3. Restart the application")
        print("4. Run migrations if needed")
    else:
        print("\n" + "=" * 50)
        print("CHECK FAILED")
        print("=" * 50)
        print("Could not access production configuration")

if __name__ == "__main__":
    main()