import os
from dataclasses import dataclass


# dataclass，语法糖，可以自动生成一些常用方法，例如:__init__ 等
# frozen=True：表示“实例创建后不可修改”（类似只读配置对象）。表示“实例创建后不可修改”（类似只读配置对象）
@dataclass(frozen=True)
class Settings:
    """运行期配置。通过环境变量加载，保持代码与环境解耦。"""
    dashscope_api_key: str
    asr_model: str = "gummy-realtime-v1"
    llm_model: str = "qwen-flash"
    ffmpeg_exe: str = r"D:\办公软件\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe"
    max_upload_size_mb: int = 5
    request_timeout_seconds: int = 30
    persist_normalized_audio: bool = False
    normalized_audio_dir: str = "tmp/normalized"


def load_settings() -> Settings:
    """
    读取并校验关键配置。
    仅 DASHSCOPE_API_KEY 为必填，其余提供合理默认值。
    """
    api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("缺少环境变量 DASHSCOPE_API_KEY")

    return Settings(
        dashscope_api_key=api_key,
        asr_model=os.getenv("ASR_MODEL", "gummy-realtime-v1"),
        llm_model=os.getenv("LLM_MODEL", "qwen-flash"),
        ffmpeg_exe=os.getenv(
            "FFMPEG_EXE",
            os.getenv(
                "FFMPEG_PATH",
                r"D:\办公软件\ffmpeg-8.1-essentials_build\bin\ffmpeg.exe",
            ),
        ),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "5")),
        request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30")),
        persist_normalized_audio=os.getenv("PERSIST_NORMALIZED_AUDIO", "false").lower() == "true",
        normalized_audio_dir=os.getenv("NORMALIZED_AUDIO_DIR", "tmp/normalized"),
    )
