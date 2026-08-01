from pathlib import Path
import json
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / '.sprint_ui_002.json'
OUTPUT_FILE = ROOT / 'PROJECT_LIVE_DASHBOARD.md'


def load_state():
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text())


def get_git_info() -> dict:
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=ROOT, text=True).strip()
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, text=True).strip()
        status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip().splitlines()
        modified = len([line for line in status if line and not line.startswith('??')])
        uncommitted = len(status)
        return {
            'branch': branch,
            'commit': commit,
            'modified_files_count': modified,
            'uncommitted_changes': uncommitted,
        }
    except Exception:
        return {}


def format_progress_bar(progress: int) -> str:
    filled = int(progress / 10)
    bar = '█' * filled + '░' * (10 - filled)
    return f'`{bar}` {progress}%'


def format_elapsed(start: str | None) -> str:
    if not start:
        return 'N/A'
    try:
        s = datetime.fromisoformat(start)
        now = datetime.now(timezone.utc)
        elapsed = now - s.astimezone(timezone.utc)
        hours = int(elapsed.total_seconds() // 3600)
        mins = int((elapsed.total_seconds() % 3600) // 60)
        return f'{hours}h {mins}m'
    except Exception:
        return 'Invalid timestamp'


def render_md(state: dict) -> str:
    git_info = get_git_info()
    lines = []

    lines.append(f"# ENGINEERING CONTROL CENTER — {state.get('sprint','')}\n")

    lines.append("## Project Information")
    lines.append(f"- **Project:** {state.get('project_name', state.get('feature','Converigo'))}")
    if state.get('project_version'):
        lines.append(f"- **Version:** {state['project_version']}")
    lines.append(f"- **Active sprint:** {state.get('sprint','')}")
    if git_info.get('branch'):
        lines.append(f"- **Branch:** {git_info['branch']}")
    if git_info.get('commit'):
        lines.append(f"- **Commit:** {git_info['commit']}")
    lines.append("")

    lines.append("## Sprint Metrics")
    lines.append(f"- **Progress:** {format_progress_bar(state.get('progress_percent', 0))}")
    lines.append(f"- **Sprint start:** {state.get('sprint_start', 'N/A')}")
    lines.append(f"- **Elapsed:** {format_elapsed(state.get('sprint_start'))}")
    lines.append(f"- **ETA:** {state.get('eta', 'N/A')}")
    lines.append("")

    lines.append("## Validation Matrix")
    validation = state.get('validation_status', {})
    for key in ['desktop', 'tablet', 'mobile', 'regression', 'performance', 'accessibility']:
        lines.append(f"- **{key.capitalize()}:** {validation.get(key, 'N/A')}")
    lines.append("")

    lines.append("## Git Status")
    lines.append(f"- **Branch:** {git_info.get('branch', 'N/A')}")
    lines.append(f"- **Latest commit:** {git_info.get('commit', 'N/A')}")
    lines.append(f"- **Modified files:** {git_info.get('modified_files_count', 0)}")
    lines.append(f"- **Uncommitted changes:** {git_info.get('uncommitted_changes', 0)}")
    lines.append("")

    lines.append("## Sprint Progress")
    lines.append(f"- **Completed:** {len(state.get('completed_tasks', []))}")
    lines.append(f"- **Remaining:** {state.get('remaining_tasks', 'N/A')}")
    lines.append("")

    lines.append("## Activity Timeline")
    events = state.get('activity_timeline', [])
    if events:
        for item in events[-10:]:
            lines.append(f"- {item.get('timestamp','')} — **{item.get('action','')}**: {item.get('details','')}")
    else:
        lines.append("- No activity recorded.")
    lines.append("")

    lines.append("## Completed Tasks")
    for t in state.get('completed_tasks', []):
        lines.append(f"- {t}")
    lines.append("")

    lines.append("## Current Task")
    lines.append(f"- {state.get('current_task','')}\n")

    lines.append("## Next Task")
    lines.append(f"- {state.get('next_task','')}\n")

    lines.append("## Modified Files")
    for f in state.get('modified_files', []):
        lines.append(f"- {f}")
    lines.append("")

    lines.append("## Validation Status")
    for k, v in validation.items():
        if k not in ['desktop', 'tablet', 'mobile', 'regression', 'performance', 'accessibility']:
            lines.append(f"- **{k.capitalize()}:** {v}")
    lines.append("")

    lines.append("## Blockers")
    if state.get('blockers'):
        for b in state.get('blockers', []):
            lines.append(f"- {b}")
    else:
        lines.append("- None")
    lines.append("")

    last_updated = state.get('last_updated') or datetime.now(timezone.utc).isoformat()
    lines.append(f"**Last updated:** {last_updated}")
    return "\n".join(lines)


def main():
    state = load_state()
    if state is None:
        print('State file missing:', STATE_FILE)
        return
    md = render_md(state)
    OUTPUT_FILE.write_text(md, encoding='utf-8')
    print('Wrote', OUTPUT_FILE)


if __name__ == '__main__':
    main()
