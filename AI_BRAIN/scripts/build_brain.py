#!/usr/bin/env python3
"""Run AI_BRAIN Repository Intelligence engines in sequence."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BrainStep:
    order: int
    name: str
    script_path: Path


ENGINE_ORDER = [
    "relationship_engine.py",
    "dependency_engine.py",
    "pattern_engine.py",
    "test_mapper.py",
    "documentation_mapper.py",
    "semantic_engine.py",
    "reasoning_context.py",
]


def ai_brain_paths() -> tuple[Path, Path]:
    """Return AI_BRAIN root and brain directory."""
    scripts_dir = Path(__file__).resolve().parent
    ai_brain_dir = scripts_dir.parent
    brain_dir = ai_brain_dir / "brain"
    return ai_brain_dir, brain_dir


def build_steps(brain_dir: Path) -> list[BrainStep]:
    """Build ordered engine step definitions."""
    return [
        BrainStep(order=index, name=script_name.removesuffix(".py"), script_path=brain_dir / script_name)
        for index, script_name in enumerate(ENGINE_ORDER, start=1)
    ]


def run_step(step: BrainStep, stop_on_error: bool) -> bool:
    """Execute one engine script and return success."""
    if not step.script_path.exists() or not step.script_path.is_file():
        print(f"[{step.order}/{len(ENGINE_ORDER)}] SKIP {step.name}: missing script")
        return False

    print(f"[{step.order}/{len(ENGINE_ORDER)}] START {step.name}")
    completed = subprocess.run([sys.executable, str(step.script_path)], capture_output=True, text=True)

    if completed.returncode == 0:
        print(f"[{step.order}/{len(ENGINE_ORDER)}] OK {step.name}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        return True

    print(f"[{step.order}/{len(ENGINE_ORDER)}] FAIL {step.name} (exit={completed.returncode})")
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip())

    if stop_on_error:
        raise SystemExit(completed.returncode)

    return False


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run AI_BRAIN Repository Intelligence engines")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop on first engine failure")
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    ai_brain_dir, brain_dir = ai_brain_paths()

    print("Repository Intelligence build started")
    print(f"AI_BRAIN directory: {ai_brain_dir.as_posix()}")

    steps = build_steps(brain_dir)
    success_count = 0

    for step in steps:
        if run_step(step, args.stop_on_error):
            success_count += 1

    print("Repository Intelligence build completed")
    print(f"Successful engines: {success_count}/{len(steps)}")


if __name__ == "__main__":
    main()
