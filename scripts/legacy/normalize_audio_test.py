import json
import shutil
import subprocess
from pathlib import Path


def get_ffmpeg_binaries():
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    return ffmpeg_path, ffprobe_path


def run_ffmpeg_convert(input_path: Path, output_path: Path) -> None:
    ffmpeg_path, _ = get_ffmpeg_binaries()
    if not ffmpeg_path:
        raise RuntimeError(
            "当前环境找不到 ffmpeg 可执行文件（shutil.which('ffmpeg') 返回空）。"
            "请确保 ffmpeg.exe 所在目录已加入 PATH，然后再运行本脚本。"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        ffmpeg_path,
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
    subprocess.run(cmd, check=True)


def probe_wav(output_path: Path) -> None:
    _, ffprobe_path = get_ffmpeg_binaries()
    if not ffprobe_path:
        print("ffprobe 未找到，跳过音频属性校验（channels/sample_rate）。")
        return

    # 只读 stream 层关键信息
    cmd = [
        ffprobe_path,
        "-v",
        "error",
        "-show_entries",
        "stream=channels,sample_rate,codec_name",
        "-of",
        "json",
        str(output_path),
    ]
    raw = subprocess.check_output(cmd)
    info = json.loads(raw.decode("utf-8", errors="replace"))
    print("ffprobe stream info:")
    print(json.dumps(info, ensure_ascii=False, indent=2))


def main():
    repo_root = Path(__file__).resolve().parents[2]
    input_path = repo_root / "raw_data" / "new" / "注塑1号机设备异常.m4a"
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{input_path}")

    output_path = repo_root / "raw_data" / "new" / "注塑1号机设备异常_16k_mono.wav"

    print("input:", input_path)
    print("output:", output_path)

    run_ffmpeg_convert(input_path, output_path)
    print("ffmpeg convert done.")

    probe_wav(output_path)
    print("done.")


if __name__ == "__main__":
    main()
