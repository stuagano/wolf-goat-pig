#!/usr/bin/env python3
"""Test script to debug sheet parsing logic"""

import requests

# Your sheet URL
csv_url = "https://docs.google.com/spreadsheets/d/1PWhi5rJ4ZGhTwySZh-D_9lo_GKJcHb1Q5MEkNasHLgM/export?format=csv&gid=474065919"

# Fetch the CSV data
response = requests.get(csv_url, timeout=30)
response.raise_for_status()
csv_text = response.text

# Parse CSV
lines = csv_text.strip().split('\n')
print(f"Total lines: {len(lines)}")
print("\nFirst 5 lines:")
for i, line in enumerate(lines[:5]):
    print(f"Line {i}: {line[:100]}...")  # First 100 chars

# Find the actual header row (looking for "Member" column)
header_line_index = -1
headers = []

for i, line in enumerate(lines):
    temp_headers = [h.strip().strip('"') for h in line.split(',')]
    # Check if this line contains the actual column headers
    if any('member' in h.lower() for h in temp_headers if h) and \
       any('quarters' in h.lower() for h in temp_headers if h):
        header_line_index = i
        headers = temp_headers
        print(f"\n✓ Found headers at row {i + 1}: {headers}")
        break

if header_line_index == -1:
    print("\n✗ Could not find headers with Member and Quarters columns")
    # Show all lines to debug
    for i, line in enumerate(lines[:10]):
        temp_headers = [h.strip().strip('"') for h in line.split(',')]
        print(f"Row {i}: {temp_headers[:7]}")  # First 7 columns

# Create header index mapping
if headers:
    header_map = {header.lower(): idx for idx, header in enumerate(headers) if header}
    print(f"\nHeader map: {header_map}")
    
    # Process a few data rows
    print("\nProcessing data rows:")
    data_count = 0
    for line in lines[header_line_index + 1:]:
        if line.strip():
            values = [v.strip().strip('"') for v in line.split(',')]
            
            # Skip empty rows or rows with too few values
            if len(values) < 2 or not any(v for v in values[:5]):
                continue
            
            # Extract player name
            player_name = None
            for name_key in ['member', 'player', 'name', 'golfer']:
                if name_key in header_map and header_map[name_key] < len(values):
                    player_name = values[header_map[name_key]]
                    break
            
            # Skip if no player name, or if it's a header/summary row
            if not player_name or player_name.lower() in ['member', 'player', 'name', '', 'total', 'average']:
                continue
            
            # Stop if we hit summary sections
            if any(keyword in player_name.lower() for keyword in ['most rounds', 'top 5', 'best score', 'worst score', 'group size']):
                print(f"Stopping at summary section: {player_name}")
                break
            
            print(f"  Player: {player_name}, Values: {values[:6]}")
            data_count += 1
            if data_count >= 5:  # Just show first 5 players
                break
    
    print(f"\nTotal players found: {data_count}")