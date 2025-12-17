#!/bin/bash
# Quick validation script for golden round - can be run from project root
cd "$(dirname "$0")/backend" && python3 tests/validate_golden_round.py
