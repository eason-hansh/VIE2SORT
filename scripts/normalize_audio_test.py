import json
from pathlib import Path

from vietsort_service.config import load_settings
from vietsort_service.services.audio import normalize_to_mono_16k_wav, resolve_ffmpeg_exe


def main():
    settings = load_settings()
    ffmpeg = resolve_ffmpeg_exe(settings.ffmpeg_exe)
    input_path = Path(r"raw_data/new/注塑1号机设备异常.m4a")
    output = normalize_to_mono_16k_wav(
        input_path=input_path,
        output_dir=Path("tmp/normalized"),
        ffmpeg_exe=ffmpeg,
        request_id="normalize_test",
    )
    print("input:", input_path)
    print("output:", output)
    print(json.dumps({"status": "ok"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
