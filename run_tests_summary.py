#!/usr/bin/env python3
"""Gather test results summary."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=no', '-q'],
    capture_output=True,
    text=True,
)

lines = result.stdout.split('\n')

# Print last 50 lines which should contain the summary
print('\n'.join(lines[-50:]))
print(f"\nExit code: {result.returncode}")
