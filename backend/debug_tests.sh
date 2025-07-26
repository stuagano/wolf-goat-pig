#!/bin/bash

set -e

echo "Testing individual commands..."

echo "1. Testing dictionary references..."
python test_dict_references.py
echo "Exit code: $?"

echo "2. Testing deployment validation..."
python deployment_validation.py
echo "Exit code: $?"

echo "3. Testing syntax check..."
python -m py_compile app/main.py
echo "Exit code: $?"

echo "4. Testing module import..."
python -c "from app.main import app; print('✅ App imported successfully')"
echo "Exit code: $?"

echo "All tests completed." 