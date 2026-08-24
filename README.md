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

### Windows 一键转换

项目目录约定：

```text
项目目录/
├── input/
│   └── sgz.nsf
├── output/
├── convert.ps1
└── convert.bat
```

将 NSF 文件放入 `input` 目录后运行：

```powershell
.\\convert.ps1 sgz.nsf
.\\convert.ps1 sgz.nsf -Duration 180 -Format mp3
convert.bat sgz.nsf -Duration 1 -Format ogg
```

脚本默认使用 OGG、180 秒和 44100 Hz。FFmpeg 与 libgme 默认路径为当前用户的安装路径；如果实际安装位置不同，请修改 `convert.ps1` 中的 `$Ffmpeg` 和 `$LibGme` 变量。源文件名只能是 `input` 目录下的文件名，不能使用绝对路径或目录分隔符。

编码临时文件现在创建在 `output` 目录所在磁盘，并通过原子替换写入最终文件，避免系统临时目录与项目输出目录跨磁盘移动时出现 `WinError 17`。

支持 `mp3` 和 `ogg` 两种格式。默认每首曲目渲染 180 秒、采样率为 44100 Hz。NSF 通常没有可靠的曲目结束标记，因此时长是固定值，可能产生尾部静音或截断循环曲目。

导出时默认会裁剪结尾连续静音：低于 `-50 dB` 且持续至少 `0.5 秒` 的尾部音频会被移除。开头静音和音乐内部停顿会保留。该功能由 FFmpeg 的 `silenceremove` 滤镜实现，不会增加 Python 依赖。低音量真实尾音可能被识别为静音；如果尾部声音高于阈值，或静音不足 `0.5 秒`，则不会裁剪。

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
