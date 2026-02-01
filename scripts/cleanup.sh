#!/bin/bash

# Sovereign Learner - Project Cleanup Script
# Removes unwanted files and caches

echo "🧹 Cleaning Sovereign Learner Project..."
echo ""

# Remove .DS_Store files (macOS metadata)
echo "Removing .DS_Store files..."
find . -name ".DS_Store" -type f -delete
echo "✅ .DS_Store files removed"

# Remove Python cache files
echo "Removing Python cache files..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -type f -delete
find . -name "*.pyo" -type f -delete
echo "✅ Python cache files removed"

# Remove temporary files
echo "Removing temporary files..."
find . -name "*.tmp" -type f -delete
find . -name "*.log" -type f -not -path "./.venv/*" -delete
echo "✅ Temporary files removed"

# Remove test files (if not needed)
echo "Checking for test files..."
if [ -f "test_tool.py" ]; then
    echo "⚠️  Found test_tool.py - consider removing if not needed"
fi

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 Current project size:"
du -sh . 2>/dev/null | awk '{print $1}'
