# NSF Audio Exporter

将 NSF 文件中的曲目通过 Game Music Emu 渲染为 PCM，再使用 FFmpeg 导出 MP3 或 OGG。

## 环境要求

- Python 3.10 或更高版本
- FFmpeg：安装后将 `ffmpeg` 加入 PATH，或通过 `--ffmpeg` 指定可执行文件
- Game_Music_Emu / libgme：
  - Windows：获取与 Python 进程架构匹配的 `gme.dll`，放入 PATH、项目目录，或通过 `--libgme` 指定路径
  - Linux：安装 `libgme.so`（常见包名为 `libgme-dev` 或对应运行时包）
  - macOS：安装 `libgme.dylib`，例如使用 Homebrew 对应包

安装测试依赖：

```powershell
python -m pip install -r requirements.txt
```

## 使用

```powershell
python -m nsf_exporter input.nsf output
python -m nsf_exporter input.nsf output --duration 30 --format ogg --sample-rate 48000
python -m nsf_exporter input.nsf output --ffmpeg C:\\tools\\ffmpeg.exe --libgme C:\\tools\\gme.dll
```

支持 `mp3` 和 `ogg` 两种格式。默认每首曲目渲染 180 秒、采样率为 44100 Hz。NSF 通常没有可靠的曲目结束标记，因此时长是固定值，可能产生尾部静音或截断循环曲目。

输出按曲目顺序使用两位数字命名，例如 `01.mp3`、`02.mp3`。如果文件已存在，则自动使用 `01_1.mp3`、`01_2.mp3` 等名称，不覆盖已有文件。

退出码：

- `0`：全部曲目成功
- `1`：至少一首曲目失败，但流程已继续
- `2`：参数、输入文件或外部依赖不可用

## 验证

运行单元测试：

```powershell
python -m pytest -q
```

真实导出还需要可用的 `gme.dll`/libgme、FFmpeg 和 NSF 样本；这些外部依赖不由 pip 安装，也不包含在本项目中。
