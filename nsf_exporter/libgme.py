import ctypes
import os
import sys
from pathlib import Path


class LibGmeError(RuntimeError):
    pass


def _library_candidates():
    if sys.platform == "win32":
        return ("gme.dll", "libgme.dll")
    if sys.platform == "darwin":
        return ("libgme.dylib", "gme.dylib")
    return ("libgme.so", "libgme.so.0")


def load_library(path=None):
    candidates = (str(path),) if path else _library_candidates()
    last_error = None
    for candidate in candidates:
        try:
            return ctypes.CDLL(candidate)
        except OSError as exc:
            last_error = exc
    raise LibGmeError(f"Unable to load libgme ({', '.join(candidates)}): {last_error}")


def _error_text(error):
    if not error:
        return None
    if isinstance(error, bytes):
        return error.decode("utf-8", errors="replace")
    return str(error)


class LibGmeRenderer:
    def __init__(self, path, sample_rate=44100, library=None):
        self.path = os.fspath(path)
        self.sample_rate = sample_rate
        self.library = library or load_library()
        self._configure_signatures()
        self._emu = ctypes.c_void_p()
        error = self.library.gme_open_file(self.path.encode(), ctypes.byref(self._emu), sample_rate)
        if _error_text(error):
            raise LibGmeError(_error_text(error))
        self._closed = False
        self.track_count = int(self.library.gme_track_count(self._emu))

    def _configure_signatures(self):
        signatures = {
            "gme_open_file": ([ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p), ctypes.c_int], ctypes.c_char_p),
            "gme_track_count": ([ctypes.c_void_p], ctypes.c_int),
            "gme_start_track": ([ctypes.c_void_p, ctypes.c_int], ctypes.c_char_p),
            "gme_set_fade": ([ctypes.c_void_p, ctypes.c_int], None),
            "gme_play": ([ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_short)], ctypes.c_char_p),
            "gme_delete": ([ctypes.c_void_p], None),
        }
        for name, (argtypes, restype) in signatures.items():
            function = getattr(self.library, name)
            try:
                function.argtypes = argtypes
                function.restype = restype
            except (AttributeError, TypeError):
                pass

    def _check(self, error):
        message = _error_text(error)
        if message:
            raise LibGmeError(message)

    def render_track(self, track_index, duration):
        if self._closed:
            raise LibGmeError("Renderer is closed")
        self._check(self.library.gme_start_track(self._emu, track_index))
        self._check(self.library.gme_set_fade(self._emu, int(duration * 1000)))
        frames = int(self.sample_rate * duration)
        output = bytearray()
        block_frames = 4096
        while frames:
            count = min(frames, block_frames)
            buffer = (ctypes.c_short * (count * 2))()
            self._check(self.library.gme_play(self._emu, count * 2, buffer))
            output.extend(bytes(buffer))
            frames -= count
        return bytes(output)

    def close(self):
        if not self._closed:
            self.library.gme_delete(self._emu)
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
