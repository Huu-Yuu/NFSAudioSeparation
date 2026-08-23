from unittest.mock import Mock

import pytest

from nsf_exporter.libgme import LibGmeError, LibGmeRenderer


@pytest.fixture
def fake_lib():
    lib = Mock()
    lib.gme_open_file.return_value = None
    lib.gme_track_count.return_value = 3
    lib.gme_start_track.return_value = None
    lib.gme_set_fade.return_value = None
    lib.gme_play.return_value = None
    lib.gme_delete.return_value = None
    return lib


def test_renderer_reads_track_count(fake_lib, tmp_path):
    renderer = LibGmeRenderer(tmp_path / "song.nsf", sample_rate=100, library=fake_lib)
    assert renderer.track_count == 3
    data = renderer.render_track(0, 1.0)
    assert len(data) == 100 * 2 * 2
    assert fake_lib.gme_play.call_args.args[1] == 200
    renderer.close()


def test_renderer_renders_across_blocks(fake_lib, tmp_path):
    renderer = LibGmeRenderer(tmp_path / "song.nsf", sample_rate=1000, library=fake_lib)
    data = renderer.render_track(0, 5.0)
    assert len(data) == 5000 * 2 * 2
    assert [call.args[1] for call in fake_lib.gme_play.call_args_list] == [4096 * 2, 904 * 2]
    renderer.close()


def test_renderer_converts_native_error(fake_lib, tmp_path):
    fake_lib.gme_start_track.side_effect = lambda *_: b"track error"
    renderer = LibGmeRenderer(tmp_path / "song.nsf", sample_rate=44100, library=fake_lib)
    with pytest.raises(LibGmeError, match="track error"):
        renderer.render_track(0, 1.0)
    renderer.close()
