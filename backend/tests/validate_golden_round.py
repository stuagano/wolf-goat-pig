#!/usr/bin/env python3
"""
Golden Round Validation Script

This script validates that the golden round has:
1. All quarters balance to zero on each hole
2. Final totals sum to zero
3. Running totals are calculated correctly
4. All 18 holes are present
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any


def load_golden_round(file_path: str) -> Dict[str, Any]:
    """Load the golden round JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def validate_hole_quarters_balance(hole: Dict[str, Any], hole_num: int) -> tuple[bool, str]:
    """
    Validate that quarters on a hole sum to zero.
    
    Returns:
        (is_valid, error_message)
    """
    quarters = hole.get('quarters', {})
    if not quarters:
        return False, f"Hole {hole_num}: Missing quarters data"
    
    total = sum(quarters.values())
    if abs(total) > 0.01:  # Allow for floating point precision
        return False, f"Hole {hole_num}: Quarters sum to {total}, expected 0. Quarters: {quarters}"
    
    return True, ""


def validate_running_totals(holes: List[Dict[str, Any]], player_ids: List[str]) -> tuple[bool, str]:
    """
    Validate that running totals are calculated correctly.
    
    Returns:
        (is_valid, error_message)
    """
    running_totals: Dict[str, int] = {pid: 0 for pid in player_ids}
    
    for i, hole in enumerate(holes, 1):
        quarters = hole.get('quarters', {})
        expected_totals = hole.get('running_totals', {})
        
        # Calculate running totals from quarters
        for pid in player_ids:
            running_totals[pid] += quarters.get(pid, 0)
        
        # Compare with expected
        for pid in player_ids:
            expected = expected_totals.get(pid, 0)
            actual = running_totals[pid]
            if expected != actual:
                return False, (
                    f"Hole {i}: Running total mismatch for {pid}. "
                    f"Expected {expected}, got {actual}. "
                    f"Quarters: {quarters}"
                )
    
    return True, ""


def validate_final_totals(holes: List[Dict[str, Any]], expected_final: Dict[str, int], player_ids: List[str]) -> tuple[bool, str]:
    """
    Validate that final totals match expected values and sum to zero.
    
    Returns:
        (is_valid, error_message)
    """
    # Calculate final totals from all quarters
    final_totals: Dict[str, int] = {pid: 0 for pid in player_ids}
    for hole in holes:
        quarters = hole.get('quarters', {})
        for pid in player_ids:
            final_totals[pid] += quarters.get(pid, 0)
    
    # Check against expected
    for pid in player_ids:
        expected = expected_final.get(pid, 0)
        actual = final_totals[pid]
        if expected != actual:
            return False, (
                f"Final total mismatch for {pid}. "
                f"Expected {expected}, got {actual}"
            )
    
    # Verify sum to zero
    total_sum = sum(final_totals.values())
    if abs(total_sum) > 0.01:
        return False, f"Final totals sum to {total_sum}, expected 0. Totals: {final_totals}"
    
    return True, ""


def validate_all_holes_present(holes: List[Dict[str, Any]]) -> tuple[bool, str]:
    """Validate that all 18 holes are present."""
    if len(holes) != 18:
        return False, f"Expected 18 holes, found {len(holes)}"
    
    hole_numbers = [h.get('hole_number') for h in holes]
    expected = list(range(1, 19))
    
    if set(hole_numbers) != set(expected):
        missing = set(expected) - set(hole_numbers)
        return False, f"Missing holes: {missing}"
    
    return True, ""


def validate_golden_round(round_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate the entire golden round.
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors: List[str] = []
    
    # Extract data
    holes = round_data.get('holes', [])
    player_ids = [p['id'] for p in round_data.get('game_metadata', {}).get('players', [])]
    expected_final = round_data.get('expected_final_totals', {})
    
    # Validation 1: All holes present
    valid, error = validate_all_holes_present(holes)
    if not valid:
        errors.append(error)
    
    # Validation 2: Each hole quarters balance to zero
    for hole in holes:
        valid, error = validate_hole_quarters_balance(hole, hole.get('hole_number', 0))
        if not valid:
            errors.append(error)
    
    # Validation 3: Running totals are correct
    if not errors:  # Only check if previous validations passed
        valid, error = validate_running_totals(holes, player_ids)
        if not valid:
            errors.append(error)
    
    # Validation 4: Final totals match and sum to zero
    if not errors:
        valid, error = validate_final_totals(holes, expected_final, player_ids)
        if not valid:
            errors.append(error)
    
    return len(errors) == 0, errors


def print_summary(round_data: Dict[str, Any]):
    """Print a summary of the golden round."""
    metadata = round_data.get('game_metadata', {})
    holes = round_data.get('holes', [])
    expected_final = round_data.get('expected_final_totals', {})
    
    print("=" * 60)
    print("GOLDEN ROUND SUMMARY")
    print("=" * 60)
    print(f"Game ID: {metadata.get('game_id')}")
    print(f"Date: {metadata.get('date')}")
    print(f"Course: {metadata.get('course')}")
    print(f"Players: {len(metadata.get('players', []))}")
    print(f"Total Holes: {len(holes)}")
    print()
    print("Final Totals:")
    for player_id, total in expected_final.items():
        player_name = next(
            (p['name'] for p in metadata.get('players', []) if p['id'] == player_id),
            player_id
        )
        print(f"  {player_name} ({player_id}): {total:+d} quarters")
    print()
    print(f"Sum of all quarters: {sum(expected_final.values())}")
    print("=" * 60)


def main():
    """Main validation function."""
    # Find the golden round file
    script_dir = Path(__file__).parent
    golden_round_path = script_dir / 'fixtures' / 'golden_round.json'
    
    if not golden_round_path.exists():
        print(f"ERROR: Golden round file not found at {golden_round_path}")
        sys.exit(1)
    
    # Load and validate
    print(f"Loading golden round from {golden_round_path}...")
    round_data = load_golden_round(str(golden_round_path))
    
    print_summary(round_data)
    print()
    
    print("Validating golden round...")
    is_valid, errors = validate_golden_round(round_data)
    
    if is_valid:
        print("✅ VALIDATION PASSED: Golden round is valid!")
        print()
        print("All checks passed:")
        print("  ✓ All 18 holes present")
        print("  ✓ Each hole's quarters sum to zero")
        print("  ✓ Running totals calculated correctly")
        print("  ✓ Final totals match expected and sum to zero")
        return 0
    else:
        print("❌ VALIDATION FAILED: Found errors:")
        print()
        for error in errors:
            print(f"  ✗ {error}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
