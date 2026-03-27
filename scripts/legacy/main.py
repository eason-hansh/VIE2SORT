import os
import shutil
import subprocess
from pathlib import Path

import dashscope
from dashscope.audio.asr import *

# 若没有将API Key配置到环境变量中，需将your-api-key替换为自己的API Key
# dashscope.api_key = "your-api-key"
dashscope.api_key = "sk-33e07c61f66d4a76a429824c7e394117"

# 输入音频：可以是 m4a/mp3/wav（会先被 ffmpeg 规范化）
INPUT_AUDIO_PATH = Path(r"raw_data/new/注塑1号机设备异常.m4a")

if not INPUT_AUDIO_PATH.exists():
    raise RuntimeError(f"找不到音频文件：{INPUT_AUDIO_PATH}")

# 解决 PATH 在不同终端/不同运行方式下不一致的问题
# 优先读取环境变量，其次使用你本机已知的 ffmpeg 绝对路径。
DEFAULT_FFMPEG_EXE = r"D:\办公软件\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe"
ffmpeg_exe = (
    os.getenv("FFMPEG_EXE")
    or os.getenv("FFMPEG_PATH")
    or DEFAULT_FFMPEG_EXE
)
if os.path.isdir(ffmpeg_exe):
    ffmpeg_exe = os.path.join(ffmpeg_exe, "ffmpeg.exe")
if not os.path.exists(ffmpeg_exe):
    ffmpeg_exe = shutil.which("ffmpeg") or ""
if not ffmpeg_exe or not os.path.exists(ffmpeg_exe):
    raise RuntimeError(
        "找不到 ffmpeg 可执行文件。"
        "请设置环境变量 FFMPEG_EXE/FFMPEG_PATH，或确认 ffmpeg.exe 已存在于默认路径。"
    )


def normalize_to_mono_16k_wav(input_path: Path) -> Path:
    """
    统一输出：mono + 16kHz + PCM S16LE 的 wav
    """
    output_path = input_path.with_suffix("").with_name(input_path.stem + "_normalized_16k_mono.wav")
    # 简单缓存：输入未更新则复用已生成的 normalized wav
    if output_path.exists() and output_path.stat().st_mtime >= input_path.stat().st_mtime:
        return output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ffmpeg_exe,
        "-y",
        "-i",
        str(input_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path


normalized_wav_path = normalize_to_mono_16k_wav(INPUT_AUDIO_PATH)

translator = TranslationRecognizerRealtime(
    model="gummy-realtime-v1",
    format="wav",
    sample_rate=16000,
    source_language="vi",
    transcription_enabled=True,
    translation_enabled=False,
    callback=None,
)

result = translator.call(str(normalized_wav_path))
error_message = getattr(result, "error_message", None)
if error_message:
    raise RuntimeError(error_message)

transcription_parts = []
for tr in getattr(result, "transcription_result_list", []) or []:
    if tr and getattr(tr, "text", None):
        transcription_parts.append(tr.text)

transcription = "\n".join(transcription_parts).strip()

print("input:", str(INPUT_AUDIO_PATH))
print("normalized:", str(normalized_wav_path))
print("format: wav")
print("transcription[vi]:", transcription)
