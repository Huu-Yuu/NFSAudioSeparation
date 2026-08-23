# NSF 曲目批量音频导出设计

## 1. 目标

构建一个 Python 命令行工具，读取一个 NSF 文件，按 NSF 内曲目顺序逐首渲染，并导出为 MP3 或 OGG。默认每首曲目渲染 180 秒，输出文件使用 `01.mp3`、`02.mp3` 等两位数字序号命名；当目标已存在时自动追加 `_1`、`_2` 等后缀。

## 2. 运行环境与依赖

### Python 依赖

项目保持 Python 层依赖最小化，`requirements.txt` 可只包含测试或类型辅助依赖；核心运行时通过标准库 `ctypes`、`wave`、`subprocess` 和 `logging` 实现。

### 原生依赖

- **Game_Music_Emu / libgme**：负责 NSF 文件识别、曲目数量查询、曲目选择和 PCM 渲染。Windows 默认查找 `gme.dll`，Linux 查找 `libgme.so`，macOS 查找 `libgme.dylib`。
- **FFmpeg**：负责临时 WAV 到 MP3/OGG 的编码。要求 `ffmpeg` 可执行文件位于 PATH，或通过命令行参数指定路径。

选择 libgme 的理由是其 NSF 播放核心成熟、支持多种 NES 音频芯片扩展，并且 C API 稳定，适合使用 `ctypes` 做轻量封装。使用 FFmpeg 可避免在 Python 中维护 MP3/OGG 编码器兼容性。

## 3. 项目结构

```text
nsf-audio-separation/
├── nsf_exporter/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── libgme.py
│   ├── audio.py
│   └── naming.py
├── tests/
│   ├── test_naming.py
│   └── test_cli.py
├── requirements.txt
└── README.md
```

## 4. 模块职责

### `cli.py`

解析以下参数：

- 位置参数 `input`：输入 NSF 文件路径。
- 位置参数 `output`：输出目录。
- `--format {mp3,ogg}`：导出格式，默认 `mp3`。
- `--duration SECONDS`：每首渲染时长，默认 `180`，必须为正数。
- `--sample-rate HZ`：PCM 采样率，默认 `44100`。
- `--ffmpeg PATH`：FFmpeg 可执行文件路径，默认从 PATH 查找。
- `--libgme PATH`：可选的 libgme 动态库路径。
- `--log-level LEVEL`：日志级别，默认 `INFO`。

CLI 负责校验输入文件、创建输出目录、初始化渲染器和编码器，并汇总每首曲目的成功与失败状态。全部成功返回 0；存在失败项返回 1；参数或运行时依赖不可用返回 2。

### `libgme.py`

通过 `ctypes.CDLL` 加载动态库，并声明使用到的 C 函数签名。封装以下操作：

1. 打开 NSF 文件并取得 `Music_Emu` 句柄。
2. 读取曲目数量。
3. 选择从 0 开始的曲目索引。
4. 设置采样率并读取交错的 16-bit stereo PCM 样本。
5. 释放句柄和动态库相关资源。

所有 libgme 返回错误字符串的 API 都转换为 Python 异常。渲染器按曲目独立创建或重置播放状态，避免上一曲目的状态泄漏到下一曲目。

### `audio.py`

负责：

1. 将 PCM 以 16-bit、little-endian、双声道 WAV 写入临时文件。
2. 调用 `ffmpeg -y` 将 WAV 转换为目标格式。
3. 将编码结果写入临时目标文件后再替换最终路径，避免留下半成品。
4. 清理临时文件。

MP3 使用固定的合理默认编码质量；OGG 使用 Vorbis 编码。编码失败时保留 FFmpeg 的 stderr 摘要并抛出带上下文的异常。

### `naming.py`

根据曲目序号和格式生成基础文件名。若基础路径已存在，则按 `_1`、`_2` 顺序寻找可用名称。命名逻辑不执行删除，因此不会覆盖用户已有文件。

## 5. 数据流

```text
NSF 文件
  -> libgme 打开并读取曲目数量
  -> 对每个曲目选择并渲染指定时长 PCM
  -> 临时 WAV
  -> FFmpeg 编码
  -> 临时目标文件
  -> 生成不冲突的序号文件名
  -> 输出目录
```

每首曲目完成后立即释放其 PCM 缓冲和临时文件，控制内存使用。日志包含输入文件、曲目总数、当前曲目、输出路径和失败原因。

## 6. 异常处理

- 输入路径不存在、不是文件或扩展名不符合预期：在开始处理前终止并给出明确提示。
- libgme 动态库缺失或无法加载：说明当前平台需要的库名、可选路径参数和安装方式。
- NSF 无法解析：终止处理，因为无法可靠确定曲目集合。
- 单首曲目渲染或编码失败：记录错误，清理该曲目的临时文件，继续处理下一首。
- FFmpeg 不存在：在首首处理前检查并终止，避免产生部分结果。
- 输出文件冲突：自动生成不冲突的新文件名。

## 7. 测试策略

- 使用纯 Python 单元测试覆盖序号命名、冲突改名、格式校验和时长/采样率校验。
- 对 libgme 和 FFmpeg 使用可注入的接口或 mock，测试成功流程、依赖缺失和单曲失败后继续处理。
- 在有真实依赖和 NSF 样本时执行一次集成测试，确认曲目数量、WAV 参数、MP3/OGG 文件可被 FFmpeg 或标准工具读取。

## 8. 已知限制

- NSF 通常没有可靠的曲目结束标记，工具按固定时长渲染；默认 180 秒可能包含尾部静音或截断循环曲目，用户可通过 `--duration` 调整。
- libgme 的动态库和 FFmpeg 是外部依赖，Windows 需要匹配 Python 进程架构的 `gme.dll`，并确保 DLL 的依赖可被系统加载。
- 不同 NSF 使用的扩展音频芯片支持程度取决于所安装的 libgme 版本。
- 输出文件为实际编码结果，不保证不同编码器版本产生完全一致的二进制文件。
