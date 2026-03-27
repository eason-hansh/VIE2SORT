import logging
import time
import uuid
from pathlib import Path

from vietsort_service.config import Settings
from vietsort_service.models import IntentResponse, StageMap, StageStatus
from vietsort_service.services.asr import transcribe_vi
from vietsort_service.services.audio import normalize_to_mono_16k_wav, resolve_ffmpeg_exe
from vietsort_service.services.llm import translate_and_classify

logger = logging.getLogger(__name__)


def run_pipeline(input_audio_path: Path, settings: Settings) -> IntentResponse:
    """
    统一处理流水线（同步）：
    normalize -> asr -> translate -> classify

    设计要点：
    - 每个阶段独立 try/except，确保“部分返回”可实现
    - stages 记录每一步 success/failed + error
    - raw 仅用于排障，默认可在上层按需关闭返回
    """
    request_id = uuid.uuid4().hex
    pipeline_start = time.perf_counter()
    timings: dict[str, int] = {}
    stages = StageMap(
        normalize=StageStatus(status="failed"),
        asr=StageStatus(status="failed"),
        translate=StageStatus(status="failed"),
        classify=StageStatus(status="failed"),
    )

    transcription_vi: str | None = None
    translation_zh: str | None = None
    intent_category: str | None = None
    reason: str | None = None
    raw: dict = {}
    normalized_path: Path | None = None

    ffmpeg_exe = resolve_ffmpeg_exe(settings.ffmpeg_exe)
    try:
        # 1) 强制音频规范化，避免源文件编码/声道导致 ASR 不稳定
        t0 = time.perf_counter()
        normalized_path = normalize_to_mono_16k_wav(
            input_path=input_audio_path,
            output_dir=Path(settings.normalized_audio_dir),
            ffmpeg_exe=ffmpeg_exe,
            request_id=request_id,
        )
        stages.normalize = StageStatus(status="success")
        timings["normalize"] = int((time.perf_counter() - t0) * 1000)
    except Exception as exc:
        stages.normalize = StageStatus(status="failed", error=str(exc))

    if stages.normalize.status == "success":
        try:
            # 2) ASR（越南语转写）
            t0 = time.perf_counter()
            transcription_vi, asr_req_id = transcribe_vi(
                str(normalized_path),
                api_key=settings.dashscope_api_key,
                model=settings.asr_model,
            )
            if asr_req_id:
                request_id = asr_req_id
            stages.asr = StageStatus(status="success")
            raw["asr"] = {"request_id": asr_req_id}
            timings["asr"] = int((time.perf_counter() - t0) * 1000)
        except Exception as exc:
            stages.asr = StageStatus(status="failed", error=str(exc))

    if stages.asr.status == "success" and transcription_vi:
        try:
            # 3) 单次 LLM 调用同时完成翻译 + 分类，减少网络往返时延
            t0 = time.perf_counter()
            translation_zh, intent_category, reason, raw_llm = translate_and_classify(
                transcription_vi=transcription_vi,
                api_key=settings.dashscope_api_key,
                model=settings.llm_model,
            )
            raw["translate"] = raw_llm
            raw["classify"] = raw_llm
            stages.translate = StageStatus(status="success")
            stages.classify = StageStatus(status="success")
            llm_elapsed = int((time.perf_counter() - t0) * 1000)
            timings["translate_classify"] = llm_elapsed
        except Exception as exc:
            stages.translate = StageStatus(status="failed", error=str(exc))
            stages.classify = StageStatus(status="failed", error=str(exc))

    # 按配置清理中间规范化文件（默认不长期保留）
    if normalized_path and normalized_path.exists() and not settings.persist_normalized_audio:
        try:
            normalized_path.unlink()
        except Exception:
            logger.warning("failed to cleanup normalized audio", extra={"extra": {"path": str(normalized_path)}})

    timings["total"] = int((time.perf_counter() - pipeline_start) * 1000)

    resp = IntentResponse(
        request_id=request_id,
        transcription_vi=transcription_vi,
        translation_zh=translation_zh,
        intent_category=intent_category,
        reason=reason,
        stages=stages,
        timings_ms=timings if timings else None,
        raw=raw or None,
    )
    return resp
