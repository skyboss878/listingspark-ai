#!/bin/bash
# Run all tests

source venv/bin/activate

echo "🧪 Running ListingSpark AI tests..."
echo ""

# Run pytest with coverage
pytest tests/ \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    -v

echo ""
echo "📊 Coverage report generated at: htmlcov/index.html"
