from pathlib import Path


def next_output_path(output_dir: Path, track_number: int, extension: str) -> Path:
    output_dir = Path(output_dir)
    extension = extension.lstrip(".")
    base = output_dir / f"{track_number:02d}.{extension}"
    if not base.exists():
        return base
    suffix = 1
    while True:
        candidate = output_dir / f"{track_number:02d}_{suffix}.{extension}"
        if not candidate.exists():
            return candidate
        suffix += 1
