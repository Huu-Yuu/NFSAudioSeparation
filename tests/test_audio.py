import wave
from pathlib import Path
from unittest.mock import patch

import pytest

from nsf_exporter.audio import AudioEncodingError, FFmpegDependencyError, encode_with_ffmpeg, write_wav


def test_write_wav_properties(tmp_path):
    path = tmp_path / "test.wav"
    write_wav(path, b"\x00\x00" * 4, 22050)
    with wave.open(str(path), "rb") as wav_file:
        assert wav_file.getnchannels() == 2
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 22050


def test_encode_mp3_invokes_ffmpeg(tmp_path):
    result = type("Result", (), {"returncode": 0, "stderr": ""})()
    observed = {}

    def run(command, **kwargs):
        from pathlib import Path
        observed["command"] = command
        Path(command[-1]).write_bytes(b"encoded")
        assert "libmp3lame" in command
        return result
    with patch("nsf_exporter.audio.subprocess.run", side_effect=run):
        encode_with_ffmpeg(b"\x00" * 16, tmp_path / "01.mp3", "mp3")
    assert observed["command"][observed["command"].index("-af") + 1] == (
        "silenceremove=stop_periods=1:stop_duration=0.5:stop_threshold=-50dB"
    )
    assert (tmp_path / "01.mp3").read_bytes() == b"encoded"


def test_encode_uses_output_directory_for_temp_files(tmp_path):
    result = type("Result", (), {"returncode": 0, "stderr": ""})()
    observed = {}

    def run(command, **kwargs):
        observed["input"] = Path(command[command.index("-i") + 1])
        Path(command[-1]).write_bytes(b"encoded")
        return result

    with patch("nsf_exporter.audio.subprocess.run", side_effect=run):
        encode_with_ffmpeg(b"\x00" * 16, tmp_path / "output" / "01.ogg", "ogg")

    assert observed["input"].parent.parent == tmp_path / "output"


def test_encode_ogg_invokes_vorbis(tmp_path):
    result = type("Result", (), {"returncode": 0, "stderr": ""})()

    observed = {}

    def run(command, **kwargs):
        from pathlib import Path
        observed["command"] = command
        Path(command[-1]).write_bytes(b"encoded")
        assert "libvorbis" in command
        return result

    with patch("nsf_exporter.audio.subprocess.run", side_effect=run):
        encode_with_ffmpeg(b"\x00" * 16, tmp_path / "01.ogg", "ogg")
    assert observed["command"][observed["command"].index("-af") + 1] == (
        "silenceremove=stop_periods=1:stop_duration=0.5:stop_threshold=-50dB"
    )
    assert (tmp_path / "01.ogg").read_bytes() == b"encoded"


def test_ffmpeg_start_failure_is_dependency_error(tmp_path):
    with patch("nsf_exporter.audio.subprocess.run", side_effect=FileNotFoundError("ffmpeg")):
        with pytest.raises(FFmpegDependencyError, match="Unable to start FFmpeg"):
            encode_with_ffmpeg(b"\x00" * 16, tmp_path / "01.mp3", "mp3")


def test_encode_failure_includes_stderr(tmp_path):
    result = type("Result", (), {"returncode": 1, "stderr": "bad codec"})()
    with patch("nsf_exporter.audio.subprocess.run", return_value=result):
        with pytest.raises(AudioEncodingError, match="bad codec"):
            encode_with_ffmpeg(b"\x00" * 16, tmp_path / "01.ogg", "ogg")
