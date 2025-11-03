#!/bin/bash
set -e

echo "Building Harvest Backup Tool..."

# Build TypeScript
echo "Step 1: Building TypeScript..."
npm run build

# Install production dependencies
echo "Step 2: Installing production dependencies..."
npm install --production

# Build Docker image
echo "Step 3: Building Docker image..."
docker build -t harvest-backup:latest .

echo "✅ Build complete! Image: harvest-backup:latest"
echo ""
echo "Run with: docker run -v \$(pwd)/backups:/app/backups harvest-backup:latest -t YOUR_TOKEN -o /app/backups"
