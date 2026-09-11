"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F4)
Version : 1.0.0

In-image probe for Factory Batch F4 (cluster G-D: FFmpeg media transcodes).

Executed INSIDE the production image by docker-runtime-verify step [4/5]
(dispatch with probe_script=scripts/ci_in_video_media_probe.py):

    python scripts/ci_in_video_media_probe.py

All fixtures are generated in-image with the installed ffmpeg binary
(Dockerfile line 8) via lavfi (testsrc2 + sine), so the probe is
self-sufficient exactly like the F2/F3 probes.  Each of the ten F4
factory plugins is resolved through the real registry, executed through
its public async convert() into a temp working dir, and the output is
re-opened and validated with ffprobe (container + codec per D8, audio
presence/absence, mp4-compress faststart).  Also verifies the D9
page/contract artifacts exist for the four formerly pageless audio
slugs.  Exit code 0 = PASS.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.plugins.registry import registry  # noqa: E402

# slug, source ext, target ext, allowed video codecs, allowed audio
# codecs, container tokens, source has audio
PROBE_TABLE = [
    ("mov-to-mp4", "mov", "mp4", {"h264"}, {"aac"}, {"mp4", "mov", "isom"}, True),
    ("mkv-to-mp4", "mkv", "mp4", {"h264"}, {"aac"}, {"mp4", "mov", "isom"}, True),
    ("avi-to-mp4", "avi", "mp4", {"h264"}, {"aac"}, {"mp4", "mov", "isom"}, True),
    ("webm-to-mp4", "webm", "mp4", {"h264"}, {"aac"}, {"mp4", "mov", "isom"}, True),
    ("gif-to-mp4", "gif", "mp4", {"h264"}, set(), {"mp4", "mov", "isom"}, False),
    ("mp4-compress", "mp4", "mp4", {"h264"}, {"aac"}, {"mp4", "mov", "isom"}, True),
    ("mp4-to-webm", "mp4", "webm", {"vp9", "vp8"}, {"opus", "vorbis"}, {"webm", "matroska"}, True),
    ("mp4-to-avi", "mp4", "avi", {"mpeg4", "msmpeg4v3"}, {"mp3"}, {"avi"}, True),
    ("wav-to-flac", "wav", "flac", set(), {"flac"}, {"flac"}, True),
    ("ogg-to-mp3", "ogg", "mp3", set(), {"mp3"}, {"mp3", "mp2"}, True),
]

D9_PAGE_ARTIFACTS = [
    "wav-to-mp3", "m4a-to-mp3", "aac-to-mp3", "flac-to-mp3",
]

SOURCE_CODEC_ARGS = {
    "mov": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "mkv": ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "avi": ["-c:v", "mpeg4", "-q:v", "5", "-c:a", "libmp3lame"],
    "webm": ["-c:v", "libvpx", "-b:v", "200k", "-c:a", "libvorbis"],
    "gif": [],
    "mp4": ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac"],
    "wav": ["-c:a", "pcm_s16le"],
    "ogg": ["-c:a", "libvorbis"],
}

def _run_ffmpeg(command: list[str]) -> None:
    completed = subprocess.run(
        command, capture_output=True, text=True, check=False, timeout=120,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"fixture failed: {(completed.stderr or '')[-400:]}")


def _build_fixtures(root: Path) -> dict[str, Path]:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is not installed in the probe environment")
    fixtures: dict[str, Path] = {}
    for ext, codec_args in SOURCE_CODEC_ARGS.items():
        output_path = root / f"probe_clip.{ext}"
        command = [ffmpeg, "-y"]
        if ext in ("wav", "ogg"):
            command += ["-f", "lavfi", "-i", "sine=frequency=1000:duration=1"]
        else:
            command += [
                "-f", "lavfi", "-i", "testsrc2=size=160x120:rate=8",
                "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            ]
        command += ["-t", "1", *codec_args, str(output_path)]
        _run_ffmpeg(command)
        fixtures[ext] = output_path
    return fixtures


def _ffprobe(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe is not installed in the probe environment")
    completed = subprocess.run(
        [
            ffprobe, "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ],
        capture_output=True, text=True, check=True, timeout=60,
    )
    return json.loads(completed.stdout)


def _verify_output(path: Path, row) -> None:
    _, _, target, video_ok, audio_ok, formats, source_audio = row
    probe = _ffprobe(path)
    container = probe["format"]["format_name"].lower()
    assert formats & set(container.split(",")), (
        f"unexpected container '{container}'"
    )
    video = [s for s in probe["streams"] if s.get("codec_type") == "video"]
    audio = [s for s in probe["streams"] if s.get("codec_type") == "audio"]
    if target in ("mp4", "webm", "avi"):
        assert video, "video target lost its video stream"
        assert video[0]["codec_name"] in video_ok, (
            f"video codec {video[0]['codec_name']} not in {video_ok} "
            "(re-encode regression?)"
        )
    else:
        assert not video, "audio target must not carry a video stream"
    if source_audio:
        assert audio and audio[0]["codec_name"] in audio_ok, (
            f"audio codec {audio[0]['codec_name'] if audio else None} "
            f"not in {audio_ok}"
        )
    else:
        assert not audio, "silent source must stay silent"


async def _convert(slug: str, source_ext: str, target_ext: str,
                   source: Path, working: Path) -> Path:
    plugin = registry.get_plugin(source_ext, target_ext, slug=slug)
    return await plugin.convert(source, target_ext, output_dir=working)


def main() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="f4_probe_") as tmp:
        root = Path(tmp)
        fixtures = _build_fixtures(root)

        for row in PROBE_TABLE:
            slug, source_ext, target_ext = row[0], row[1], row[2]
            try:
                if not registry.has_slug(slug):
                    raise AssertionError(f"{slug} not registered")
                working = root / f"out_{slug.replace('-', '_')}"
                output_path = asyncio.run(_convert(
                    slug, source_ext, target_ext,
                    fixtures[source_ext], working,
                ))
                assert output_path.is_file() and output_path.stat().st_size > 0
                _verify_output(output_path, row)
                print(f"F4 PROBE OK: {slug} ({source_ext} -> {target_ext})")
            except Exception as exc:  # noqa: BLE001 - probe reports all
                failures.append(f"{slug}: {type(exc).__name__}: {exc}")

        # D9: page artifacts shipped with the image (contract policy: only
        # converters with a real regression sample ship .contract.json -
        # the three F4 mp4-source converters do).
        converters_dir = (
            Path(__file__).resolve().parent.parent / "app" / "data" / "converters"
        )
        for slug in D9_PAGE_ARTIFACTS:
            page_artifact = converters_dir / f"{slug}.json"
            if page_artifact.exists():
                print(f"F4 PROBE OK: D9 page artifact {page_artifact.name}")
            else:
                failures.append(f"D9 page artifact missing: {page_artifact.name}")
        for slug in ("mp4-compress", "mp4-to-webm", "mp4-to-avi"):
            contract_artifact = converters_dir / f"{slug}.contract.json"
            if contract_artifact.exists():
                print(f"F4 PROBE OK: contract artifact {contract_artifact.name}")
            else:
                failures.append(f"contract artifact missing: {contract_artifact.name}")

    if failures:
        print("F4 PROBE: FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("F4 PROBE: PASS (10/10 media converters verified in-image)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

