#!/usr/bin/env python3
"""Execute AI_BRAIN metadata pipeline in required order."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from common import ai_brain_dir


@dataclass(frozen=True)
class PipelineStep:
    order: int
    module_name: str
    script_name: str


PIPELINE = [
    PipelineStep(1, "project_scanner", "project_scanner.py"),
    PipelineStep(2, "project_map", "project_map.py"),
    PipelineStep(3, "knowledge_builder", "knowledge_builder.py"),
    PipelineStep(4, "module_summary", "module_summary.py"),
    PipelineStep(5, "route_scanner", "route_scanner.py"),
    PipelineStep(6, "service_scanner", "service_scanner.py"),
    PipelineStep(7, "converter_scanner", "converter_scanner.py"),
    PipelineStep(8, "context_builder", "context_builder.py"),
    PipelineStep(9, "health_check", "health_check.py"),
]


def run_step(step: PipelineStep, repo_root: Path, scripts_dir: Path, stop_on_error: bool) -> bool:
    """Run a single pipeline step and return success state."""
    script_path = scripts_dir / step.script_name

    if not script_path.exists() or not script_path.is_file():
        print(f"[{step.order}/9] SKIP {step.module_name}: script missing ({script_path.as_posix()})")
        return False

    cmd = [sys.executable, str(script_path), "--root", str(repo_root)]
    if step.module_name in {"knowledge_builder", "module_summary", "context_builder", "health_check"}:
        cmd = [sys.executable, str(script_path)]

    print(f"[{step.order}/9] START {step.module_name}")
    completed = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_root)

    if completed.returncode == 0:
        print(f"[{step.order}/9] OK {step.module_name}")
        if completed.stdout.strip():
            print(completed.stdout.strip())
        return True

    print(f"[{step.order}/9] FAIL {step.module_name} (exit={completed.returncode})")
    if completed.stdout.strip():
        print(completed.stdout.strip())
    if completed.stderr.strip():
        print(completed.stderr.strip())

    if stop_on_error:
        raise SystemExit(completed.returncode)

    return False


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run AI_BRAIN metadata pipeline")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--stop-on-error", action="store_true", help="Stop on first failed step")
    return parser.parse_args()


def main() -> None:
    """Program entry point."""
    args = parse_args()
    repo_root = args.root.resolve()

    if not repo_root.exists() or not repo_root.is_dir():
        raise SystemExit(f"Invalid --root directory: {repo_root}")

    scripts_dir = ai_brain_dir() / "scripts"
    success_count = 0

    print("AI_BRAIN build started")
    print(f"Repository root: {repo_root.as_posix()}")

    for step in PIPELINE:
        success = run_step(step, repo_root, scripts_dir, args.stop_on_error)
        if success:
            success_count += 1

    print("AI_BRAIN build completed")
    print(f"Successful steps: {success_count}/{len(PIPELINE)}")


if __name__ == "__main__":
    main()
