# NSF 音频导出实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个 Windows 优先、可跨平台运行的 Python CLI，将 NSF 中的每首曲目通过 libgme 渲染并编码为 MP3 或 OGG。

**Architecture:** 使用标准库 `ctypes` 封装 libgme C API，使用 `wave` 生成临时 PCM WAV，再通过 FFmpeg 子进程编码。CLI 负责参数校验、依赖检查、逐曲目调度、日志和退出码；命名模块负责序号文件名及冲突自动改名。

**Tech Stack:** Python 3.10+、`ctypes`、`wave`、`argparse`、`subprocess`、`logging`、pytest、Game_Music_Emu/libgme、FFmpeg。

---

### Task 1: 创建项目骨架和参数模型

**Files:**
- Create: `nsf_exporter/__init__.py`
- Create: `nsf_exporter/__main__.py`
- Create: `nsf_exporter/cli.py`
- Create: `requirements.txt`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 编写参数解析和校验测试**

测试 `build_parser()` 和 `validate_args()`：默认格式为 `mp3`、默认时长为 `180`、默认采样率为 `44100`；负时长、零采样率和非法格式必须被 `argparse` 拒绝。

```python
def test_parser_defaults(tmp_path):
    args = build_parser().parse_args([str(tmp_path / "song.nsf"), str(tmp_path / "out")])
    assert args.format == "mp3"
    assert args.duration == 180.0
    assert args.sample_rate == 44100


def test_parser_rejects_invalid_format(tmp_path):
    with pytest.raises(SystemExit):
        build_parser().parse_args(["song.nsf", "out", "--format", "wav"])
```

- [ ] **Step 2: 运行测试确认失败**

运行：`python -m pytest tests/test_cli.py -q`

预期：因模块或解析器尚未定义而失败。

- [ ] **Step 3: 实现最小 CLI 骨架**

定义 `build_parser()`、正数参数转换器 `positive_float()`/`positive_int()`，并让 `main()` 暂时完成参数解析、日志初始化和入口返回。`__main__.py` 使用 `raise SystemExit(main())`。

- [ ] **Step 4: 运行测试确认通过**

运行：`python -m pytest tests/test_cli.py -q`

预期：参数相关测试通过。

### Task 2: 实现不冲突的序号命名

**Files:**
- Create: `nsf_exporter/naming.py`
- Test: `tests/test_naming.py`

- [ ] **Step 1: 编写命名测试**

覆盖 `01.mp3`、`02.ogg` 的基础命名和已存在文件时的 `01_1.mp3`、`01_2.mp3` 递增命名。

```python
def test_next_output_path_adds_suffix(tmp_path):
    (tmp_path / "01.mp3").touch()
    (tmp_path / "01_1.mp3").touch()
    assert next_output_path(tmp_path, 1, "mp3").name == "01_2.mp3"
```

- [ ] **Step 2: 运行测试确认失败**

运行：`python -m pytest tests/test_naming.py -q`

预期：因 `naming.py` 尚未实现而失败。

- [ ] **Step 3: 实现 `next_output_path()`**

使用两位零填充曲目序号；优先返回基础路径，随后按从 1 开始的后缀查找第一个不存在的路径。不删除、不覆盖已有文件。

- [ ] **Step 4: 运行测试确认通过**

运行：`python -m pytest tests/test_naming.py -q`

预期：命名测试通过。

### Task 3: 封装 libgme 动态库和 NSF 渲染

**Files:**
- Create: `nsf_exporter/libgme.py`
- Test: `tests/test_libgme.py`

- [ ] **Step 1: 编写可替换动态库接口测试**

使用 fake library object 验证 `LibGmeRenderer` 设置函数签名、打开文件、读取曲目数量、选择曲目和按 `sample_rate * duration` 读取 stereo samples；libgme 返回错误字符串时转换为 `LibGmeError`。

```python
def test_renderer_reads_track_count(fake_lib, nsf_path):
    renderer = LibGmeRenderer(nsf_path, sample_rate=44100, library=fake_lib)
    assert renderer.track_count == 3


def test_renderer_converts_native_error(fake_lib, nsf_path):
    fake_lib.gme_start_track.side_effect = lambda *_: b"track error"
    renderer = LibGmeRenderer(nsf_path, sample_rate=44100, library=fake_lib)
    with pytest.raises(LibGmeError, match="track error"):
        renderer.render_track(0, 1.0)
```

- [ ] **Step 2: 运行测试确认失败**

运行：`python -m pytest tests/test_libgme.py -q`

预期：因渲染封装尚未实现而失败。

- [ ] **Step 3: 实现 C API 封装**

实现动态库候选路径选择、`ctypes` 签名声明、资源释放和异常转换。封装至少包含 `gme_open_file`、`gme_track_count`、`gme_start_track`、`gme_set_fade`、`gme_play`、`gme_type`/必要加载函数和 `gme_delete`。`render_track()` 以固定采样率和时长循环读取 PCM，返回 `bytes`；使用 16-bit stereo 样本格式。

- [ ] **Step 4: 运行测试确认通过**

运行：`python -m pytest tests/test_libgme.py -q`

预期：fake library 单元测试通过。

### Task 4: 实现 WAV 写入和 FFmpeg 编码

**Files:**
- Create: `nsf_exporter/audio.py`
- Test: `tests/test_audio.py`

- [ ] **Step 1: 编写音频测试**

验证 WAV 为 2 声道、16-bit、指定采样率，并 mock `subprocess.run` 检查 MP3/OGG 的 FFmpeg 参数、错误输出和临时文件清理。

- [ ] **Step 2: 运行测试确认失败**

运行：`python -m pytest tests/test_audio.py -q`

预期：因音频模块尚未实现而失败。

- [ ] **Step 3: 实现 `write_wav()` 和 `encode_with_ffmpeg()`**

使用 `tempfile.TemporaryDirectory` 管理 WAV 和编码临时文件；`write_wav()` 使用标准库 `wave`；编码命令使用 `ffmpeg -y -hide_banner -loglevel error -i input.wav`，MP3 添加 `-codec:a libmp3lame -q:a 2`，OGG 添加 `-codec:a libvorbis -q:a 5`。使用 `subprocess.run(..., check=False, capture_output=True, text=True)`，非零退出时抛出包含 stderr 的 `AudioEncodingError`。

- [ ] **Step 4: 运行测试确认通过**

运行：`python -m pytest tests/test_audio.py -q`

预期：WAV 和编码测试通过。

### Task 5: 组装逐曲目导出流程和 CLI 退出码

**Files:**
- Modify: `nsf_exporter/cli.py`
- Modify: `nsf_exporter/__main__.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 编写导出流程测试**

注入 fake renderer 和 fake encoder，验证曲目按 0 到 `track_count - 1` 顺序处理、生成不冲突路径、单首失败后继续，并在有失败时返回 1；输入或依赖检查失败返回 2。

- [ ] **Step 2: 运行测试确认失败**

运行：`python -m pytest tests/test_cli.py -q`

预期：导出流程尚未接入而失败。

- [ ] **Step 3: 实现 `export_tracks()` 和完整 `main()`**

处理前检查输入文件、输出目录、FFmpeg 可执行文件和 libgme 加载；构造 renderer，记录总曲目数；每首曲目调用 `render_track()`、`write_wav()` 和 `encode_with_ffmpeg()`，目标路径由 `next_output_path()` 得到；捕获单曲异常后继续，输出汇总日志并返回对应退出码。

- [ ] **Step 4: 运行全部测试**

运行：`python -m pytest -q`

预期：所有单元测试通过。

### Task 6: 编写依赖安装和使用说明

**Files:**
- Create: `README.md`
- Modify: `requirements.txt`

- [ ] **Step 1: 编写 README**

说明 Python 版本、Windows 获取并放置 `gme.dll` 的方式、FFmpeg 安装与 PATH 配置、Linux/macOS 动态库名称、命令格式、格式和时长示例、输出冲突命名、退出码及 NSF 固定时长限制。

- [ ] **Step 2: 完善 requirements.txt**

列出运行或测试实际使用的 Python 依赖，避免把 FFmpeg 或 libgme 误写成可由 pip 安装的依赖。

- [ ] **Step 3: 运行帮助命令和静态验证**

运行：`python -m nsf_exporter --help`

预期：显示输入路径、输出目录、`--format`、`--duration`、`--sample-rate`、`--ffmpeg` 和 `--libgme` 参数。

### Task 7: 集成验证

**Files:**
- Modify: `nsf_exporter/libgme.py`（仅在集成验证发现 API 签名问题时）
- Modify: `tests/`（仅补充针对实际问题的测试）

- [ ] **Step 1: 检查本机外部依赖**

运行：`where.exe ffmpeg`，并确认可加载的 `gme.dll` 或用户指定的 libgme 路径。

- [ ] **Step 2: 使用真实 NSF 样本执行短时导出**

运行：`python -m nsf_exporter sample.nsf output --duration 1 --format ogg`

预期：按曲目数量生成可读取的 OGG 文件，文件名从 `01.ogg` 开始；已有文件会自动改名。

- [ ] **Step 3: 使用 FFprobe 验证音频属性**

运行：`ffprobe -v error -show_streams output\01.ogg`

预期：音频流为 Vorbis、双声道、目标采样率，并且时长接近 1 秒。

- [ ] **Step 4: 汇总测试结果**

运行：`python -m pytest -q`

预期：单元测试和可用环境下的集成验证均通过；若本机缺少外部依赖，明确记录未执行原因。
