from __future__ import annotations
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / '.sprint_ui_002.json'
DASH_SCRIPT = ROOT / 'scripts' / 'update_sprint_dashboard.py'


def load_state() -> dict:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f'State file missing: {STATE_FILE}')
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict) -> None:
    state['last_updated'] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2) + '\n')


def run_dashboard() -> None:
    subprocess.run([sys.executable, str(DASH_SCRIPT)], check=True)


def complete_task(state: dict, task: str) -> str:
    tasks = state.setdefault('completed_tasks', [])
    if task not in tasks:
        tasks.append(task)
        if state.get('current_task') == task:
            state['current_task'] = ''
        return f'Completed task: {task}'
    return f'Task already completed: {task}'


def start_task(state: dict, task: str) -> str:
    state['current_task'] = task
    if state.get('next_task') == task:
        state['next_task'] = ''
    return f'Started task: {task}'


def set_next(state: dict, task: str) -> str:
    state['next_task'] = task
    return f'Next task set to: {task}'


def set_progress(state: dict, percent: int) -> str:
    state['progress_percent'] = max(0, min(100, percent))
    return f'Progress set to: {state["progress_percent"]}%'


def set_blocker(state: dict, message: str) -> str:
    state['blockers'] = [message] if message else []
    return f'Blocker set to: {message}'


def clear_blocker(state: dict) -> str:
    state['blockers'] = []
    return 'Blockers cleared.'


def add_file(state: dict, path: str) -> str:
    files = state.setdefault('modified_files', [])
    if path not in files:
        files.append(path)
        return f'Added modified file: {path}'
    return f'File already present: {path}'


def set_validation(state: dict, which: str, status: str) -> str:
    vs = state.setdefault('validation_status', {})
    vs[which] = status
    return f'Validation {which} set to {status}'


def set_project(state: dict, name: str, version: str | None) -> str:
    state['project_name'] = name
    if version:
        state['project_version'] = version
    return f'Project set to {name}' + (f' version {version}' if version else '')


def set_sprint_start(state: dict, timestamp: str) -> str:
    state['sprint_start'] = timestamp
    return f'Sprint start set to {timestamp}'


def set_eta(state: dict, timestamp: str) -> str:
    state['eta'] = timestamp
    return f'ETA set to {timestamp}'


def add_activity(state: dict, action: str, details: str) -> str:
    events = state.setdefault('activity_timeline', [])
    events.append({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': action,
        'details': details,
    })
    return f'Activity added: {action} - {details}'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Update sprint state and regenerate the dashboard.'
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    complete = subparsers.add_parser('complete', help='Mark a task complete')
    complete.add_argument('task', help='Task name')

    start = subparsers.add_parser('start', help='Start a task')
    start.add_argument('task', help='Task name')

    nxt = subparsers.add_parser('next', help='Set the next task')
    nxt.add_argument('task', help='Next task name')

    progress = subparsers.add_parser('progress', help='Set progress percent')
    progress.add_argument('percent', type=int, help='Progress value 0-100')

    blocker = subparsers.add_parser('blocker', help='Set a blocker message')
    blocker.add_argument('message', help='Blocker message')

    subparsers.add_parser('clear-blocker', help='Clear blocker messages')

    file_cmd = subparsers.add_parser('file', help='Add a modified file path')
    file_cmd.add_argument('path', help='File path')

    validation = subparsers.add_parser('validation', help='Set validation status')
    validation.add_argument('which', choices=['desktop', 'tablet', 'mobile', 'regression', 'performance', 'accessibility', 'multi_file', 'responsive'], help='Validation area')
    validation.add_argument('status', choices=['PASS', 'FAIL', 'WARN', 'PENDING'], help='Validation status')

    project = subparsers.add_parser('project', help='Set project metadata')
    project.add_argument('name', help='Project name')
    project.add_argument('--version', help='Project version', default=None)

    activity = subparsers.add_parser('activity', help='Append an activity timeline event')
    activity.add_argument('action', help='Action name')
    activity.add_argument('details', help='Details for the activity')

    sprint_start = subparsers.add_parser('sprint-start', help='Set sprint start timestamp')
    sprint_start.add_argument('timestamp', help='ISO timestamp for sprint start')

    eta = subparsers.add_parser('eta', help='Set sprint ETA timestamp')
    eta.add_argument('timestamp', help='ISO timestamp for ETA')

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        state = load_state()
    except FileNotFoundError as exc:
        print(exc)
        return 1

    if args.command == 'complete':
        summary = complete_task(state, args.task)
    elif args.command == 'start':
        summary = start_task(state, args.task)
    elif args.command == 'next':
        summary = set_next(state, args.task)
    elif args.command == 'progress':
        summary = set_progress(state, args.percent)
    elif args.command == 'blocker':
        summary = set_blocker(state, args.message)
    elif args.command == 'clear-blocker':
        summary = clear_blocker(state)
    elif args.command == 'file':
        summary = add_file(state, args.path)
    elif args.command == 'validation':
        summary = set_validation(state, args.which, args.status)
    elif args.command == 'project':
        summary = set_project(state, args.name, args.version)
    elif args.command == 'activity':
        summary = add_activity(state, args.action, args.details)
    elif args.command == 'sprint-start':
        summary = set_sprint_start(state, args.timestamp)
    elif args.command == 'eta':
        summary = set_eta(state, args.timestamp)
    else:
        print('Unknown command')
        return 1

    save_state(state)
    try:
        run_dashboard()
    except subprocess.CalledProcessError:
        print('Failed to regenerate dashboard file.')
        return 1

    print(summary)
    print('Saved .sprint_ui_002.json and regenerated PROJECT_LIVE_DASHBOARD.md.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
