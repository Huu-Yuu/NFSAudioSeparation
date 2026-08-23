from nsf_exporter.naming import next_output_path


def test_next_output_path_basic(tmp_path):
    assert next_output_path(tmp_path, 1, "mp3").name == "01.mp3"
    assert next_output_path(tmp_path, 2, "ogg").name == "02.ogg"


def test_next_output_path_adds_suffix(tmp_path):
    (tmp_path / "01.mp3").touch()
    (tmp_path / "01_1.mp3").touch()
    assert next_output_path(tmp_path, 1, "mp3").name == "01_2.mp3"
