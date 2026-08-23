import pytest

from nsf_exporter.audio import FFmpegDependencyError
from nsf_exporter.cli import build_parser, export_tracks


def test_parser_defaults(tmp_path):
    args = build_parser().parse_args([str(tmp_path / "song.nsf"), str(tmp_path / "out")])
    assert args.format == "mp3"
    assert args.duration == 180.0
    assert args.sample_rate == 44100


def test_parser_rejects_invalid_format():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["song.nsf", "out", "--format", "wav"])


@pytest.mark.parametrize("option,value", [
    ("--duration", "0"),
    ("--duration", "-1"),
    ("--duration", "nan"),
    ("--duration", "inf"),
    ("--duration", "-inf"),
    ("--sample-rate", "0"),
])
def test_parser_rejects_non_positive_or_non_finite(option, value):
    with pytest.raises(SystemExit):
        build_parser().parse_args(["song.nsf", "out", option, value])


def test_export_closes_renderer_after_track_failure(tmp_path):
    class Renderer:
        track_count = 1

        def __init__(self):
            self.closed = False

        def render_track(self, index, duration):
            raise RuntimeError("render failed")

        def close(self):
            self.closed = True

    renderer = Renderer()
    args = type("Args", (), {
        "input": tmp_path / "song.nsf", "output": tmp_path / "out", "format": "mp3",
        "duration": 1.0, "sample_rate": 44100, "ffmpeg": "ffmpeg", "libgme": None,
    })()
    assert export_tracks(args, renderer_factory=lambda *args, **kwargs: renderer,
                         library_loader=lambda _: object()) == 1
    assert renderer.closed


def test_export_returns_dependency_error_and_closes_renderer(tmp_path):
    class Renderer:
        track_count = 1

        def __init__(self):
            self.closed = False

        def render_track(self, index, duration):
            return b"pcm"

        def close(self):
            self.closed = True

    renderer = Renderer()
    args = type("Args", (), {
        "input": tmp_path / "song.nsf", "output": tmp_path / "out", "format": "ogg",
        "duration": 1.0, "sample_rate": 44100, "ffmpeg": "missing-ffmpeg", "libgme": None,
    })()

    def encoder(*args, **kwargs):
        raise FFmpegDependencyError("not found")

    assert export_tracks(args, renderer_factory=lambda *args, **kwargs: renderer,
                         encoder=encoder, library_loader=lambda _: object()) == 2
    assert renderer.closed
