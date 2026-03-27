import os
import shutil
import subprocess
import uuid
from pathlib import Path


def resolve_ffmpeg_exe(configured_path: str) -> str:
    """
    按优先级解析 ffmpeg 可执行文件：
    1) 配置路径（可为目录或完整 exe）
    2) 系统 PATH 中的 ffmpeg
    """
    ffmpeg_exe = configured_path
    if os.path.isdir(ffmpeg_exe):
        ffmpeg_exe = os.path.join(ffmpeg_exe, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        return ffmpeg_exe
    found = shutil.which("ffmpeg")
    if found:
        return found
    raise RuntimeError("找不到 ffmpeg 可执行文件，请配置 FFMPEG_EXE 或系统 PATH。")


def normalize_to_mono_16k_wav(
    input_path: Path,
    output_dir: Path,
    ffmpeg_exe: str,
    request_id: str,
) -> Path:
    """
    将任意输入音频统一转为：
    - 单声道（mono）
    - 16kHz
    - PCM S16LE WAV
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{request_id}_{uuid.uuid4().hex[:8]}_normalized.wav"

    # 统一 normalize 参数，保证下游 ASR 输入稳定
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
