#!/bin/bash
# Setup script for School Operations Environment

set -e

echo "🎓 Setting up School Operations Environment..."
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✅ Installation complete!"
echo ""
echo "To get started:"
echo "  1. Run validation: python validate_environment.py"
echo "  2. Run tests: python test_environment.py"
echo "  3. Start interactive app: python app.py"
echo "  4. Run baseline: export HF_TOKEN='your-key' && python baseline_inference.py"
echo ""
