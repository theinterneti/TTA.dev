#!/usr/bin/env python3
"""
Check the status of the comprehensive model test and generate a report when complete.
"""

import json
import subprocess
import time

# Configuration
RESULTS_FILE = "/app/model_test_results/comprehensive_test_results.json"
VISUALIZATION_SCRIPT = "/app/scripts/visualize_test_results.py"
OUTPUT_DIR = "/app/model_test_results/visualizations"
CHECK_INTERVAL = 300  # 5 minutes


def load_results():
    """Load the current test results."""
    try:
        with open(RESULTS_FILE) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
        return None


def count_completed_tests(results):
    """Count the number of completed tests."""
    if not results or "results" not in results:
        return 0
    return len(results["results"])


def calculate_expected_tests(results):
    """Calculate the expected number of tests."""
    if not results:
        return 0

    num_models = len(results.get("models", []))
    num_quantizations = len(results.get("quantizations", []))
    num_temperatures = len(results.get("temperatures", []))

    return num_models * num_quantizations * num_temperatures


def generate_report():
    """Generate the visualization report."""
    cmd = ["python3", VISUALIZATION_SCRIPT, "--results", RESULTS_FILE, "--output-dir", OUTPUT_DIR]

    try:
        subprocess.run(cmd, check=True)
        print(f"Report generated successfully at {OUTPUT_DIR}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating report: {e}")
        return False


def main():
    """Main function."""
    print(f"Monitoring test progress in {RESULTS_FILE}")

    while True:
        results = load_results()

        if not results:
            print("No results file found yet. Waiting...")
            time.sleep(CHECK_INTERVAL)
            continue

        completed = count_completed_tests(results)
        expected = calculate_expected_tests(results)

        if expected == 0:
            print("Could not determine expected test count. Waiting...")
            time.sleep(CHECK_INTERVAL)
            continue

        progress = (completed / expected) * 100
        print(f"Progress: {completed}/{expected} tests completed ({progress:.1f}%)")

        # Check if all tests are complete
        if completed >= expected:
            print("All tests complete! Generating report...")
            generate_report()
            break

        # Wait before checking again
        print(f"Waiting {CHECK_INTERVAL / 60:.1f} minutes before next check...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
