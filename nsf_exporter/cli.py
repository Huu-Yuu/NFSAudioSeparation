import argparse
import logging
import math
import shutil
from pathlib import Path

from .audio import AudioEncodingError, FFmpegDependencyError, encode_with_ffmpeg
from .libgme import LibGmeError, LibGmeRenderer, load_library
from .naming import next_output_path


def positive_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render NSF tracks to MP3 or OGG audio.")
    parser.add_argument("input", type=Path, help="input NSF file")
    parser.add_argument("output", type=Path, help="output directory")
    parser.add_argument("--format", choices=("mp3", "ogg"), default="mp3")
    parser.add_argument("--duration", type=positive_float, default=180.0)
    parser.add_argument("--sample-rate", type=positive_int, default=44100)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--libgme", default=None)
    parser.add_argument("--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR"))
    return parser


def export_tracks(args, renderer_factory=LibGmeRenderer, encoder=encode_with_ffmpeg, library_loader=load_library) -> int:
    logger = logging.getLogger(__name__)
    try:
        renderer = renderer_factory(args.input, sample_rate=args.sample_rate, library=library_loader(args.libgme))
    except Exception as exc:
        logger.error("Unable to initialize libgme: %s", exc)
        return 2
    successes = 0
    failures = 0
    try:
        for index in range(renderer.track_count):
            destination = next_output_path(args.output, index + 1, args.format)
            try:
                pcm = renderer.render_track(index, args.duration)
                encoder(pcm, destination, args.format, ffmpeg=args.ffmpeg, sample_rate=args.sample_rate)
                successes += 1
                logger.info("Exported track %d to %s", index + 1, destination)
            except FFmpegDependencyError as exc:
                logger.error("FFmpeg dependency failed: %s", exc)
                return 2
            except Exception as exc:
                failures += 1
                logger.error("Track %d failed: %s", index + 1, exc)
    finally:
        renderer.close()
    logger.info("Export complete: %d succeeded, %d failed", successes, failures)
    return 1 if failures else 0


def validate_args(args) -> None:
    if not args.input.is_file():
        raise ValueError(f"Input NSF file does not exist: {args.input}")
    args.output.mkdir(parents=True, exist_ok=True)
    if shutil.which(args.ffmpeg) is None and not Path(args.ffmpeg).is_file():
        raise ValueError(f"FFmpeg executable not found: {args.ffmpeg}")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")
    try:
        validate_args(args)
        return export_tracks(args)
    except (ValueError, OSError, LibGmeError, AudioEncodingError) as exc:
        logging.getLogger(__name__).error("%s", exc)
        return 2
