import os
import subprocess
import tempfile
import wave
from pathlib import Path


class AudioEncodingError(RuntimeError):
    pass


class FFmpegDependencyError(AudioEncodingError):
    pass


def write_wav(path, pcm_data, sample_rate):
    with wave.open(os.fspath(path), "wb") as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)


def encode_with_ffmpeg(pcm_data, output_path, format_name, ffmpeg="ffmpeg", sample_rate=44100):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_path.parent) as temp_dir:
        wav_path = Path(temp_dir) / "input.wav"
        encoded_path = Path(temp_dir) / f"output.{format_name}"
        write_wav(wav_path, pcm_data, sample_rate)
        command = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav_path)]
        if format_name == "mp3":
            command += ["-codec:a", "libmp3lame", "-q:a", "2"]
        elif format_name == "ogg":
            command += ["-codec:a", "libvorbis", "-q:a", "5"]
        else:
            raise AudioEncodingError(f"Unsupported format: {format_name}")
        command.append(str(encoded_path))
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
        except OSError as exc:
            raise FFmpegDependencyError(f"Unable to start FFmpeg: {exc}") from exc
        if result.returncode != 0:
            detail = result.stderr.strip() or "unknown FFmpeg error"
            raise AudioEncodingError(f"FFmpeg encoding failed: {detail}")
        if not encoded_path.is_file():
            raise AudioEncodingError("FFmpeg did not produce an output file")
        os.replace(encoded_path, output_path)
