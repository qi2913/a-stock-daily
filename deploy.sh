#!/bin/bash
# Deploy to GitHub Pages
# Usage: ./deploy.sh <github-username> <repo-name>
# Example: ./deploy.sh WangJiaQi34 a-stock-daily

set -e

USERNAME="${1:-WangJiaQi34}"
REPO="${2:-a-stock-daily}"

echo "🚀 Deploying to GitHub Pages..."
echo "   Repository: git@github.com:${USERNAME}/${REPO}.git"

# Run the report first
cd "$(dirname "$0")"
./.venv/bin/python run.py --mode all

# Check if gh-pages branch exists
if git remote get-url origin 2>/dev/null; then
    echo "📡 Remote exists, pushing..."
else
    echo "🔗 Adding remote..."
    git remote add origin "git@github.com:${USERNAME}/${REPO}.git"
fi

# Create gh-pages branch with site content
git checkout -B gh-pages 2>/dev/null || git checkout gh-pages
git rm -rf . 2>/dev/null || true
cp -r output/site/* .
git add .
git commit -m "Deploy: $(date '+%Y-%m-%d %H:%M')" || echo "No changes"
git push origin gh-pages --force

git checkout master 2>/dev/null || git checkout main

echo ""
echo "✅ Deployed! Visit: https://${USERNAME}.github.io/${REPO}/"
echo "⏱️  It may take 1-2 minutes for GitHub Pages to update."
